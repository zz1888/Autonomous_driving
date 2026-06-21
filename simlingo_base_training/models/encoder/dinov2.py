import torch
import torch.nn.functional as F
from torch import nn
from transformers import AutoModel


class MotionTokenEncoder(nn.Module):
    def __init__(self, embed_dim: int, num_motion_tokens: int = 8):
        super().__init__()
        self.num_motion_tokens = num_motion_tokens
        self.embed_dim = embed_dim
        self.encoder = nn.Sequential(
            nn.LayerNorm(embed_dim),
            nn.Linear(embed_dim, embed_dim // 4),
            nn.SiLU(),
            nn.Linear(embed_dim // 4, embed_dim),
        )
        self.query = nn.Parameter(torch.randn(num_motion_tokens, embed_dim) * 0.02)

    def forward(self, diff: torch.Tensor) -> torch.Tensor:
        bs, num_cams, n_tokens, channels = diff.shape
        motion = self.encoder(diff)                                    # [B, C, N, D]
        motion = motion.view(bs, num_cams * n_tokens, channels)        # [B, N, D]
        scale = self.embed_dim ** 0.5
        attn = torch.softmax(motion @ self.query.T / scale, dim=1)    # [B, N, K]
        return torch.einsum('bnk,bnd->bkd', attn, motion)             # [B, K, D]


class DINOv2EncoderModel(nn.Module):
    """DINOv2-L/14 encoder with the same output contract as the LLaVA-Next encoder.

    Input shape: [B, T, N, P, C, H, W]. For DINO, P is expected to be 1.
    Output: current-frame visual tokens plus optional compact motion tokens.
    """

    def __init__(
        self,
        variant: str,
        embed_dim: int,
        freeze: bool = True,
        downsample_feature_grid_factor: int = 2,
        use_global_img: bool = False,
        num_motion_tokens: int = 8,
    ):
        super().__init__()
        self.num_cameras = 1
        self.num_frames = 1
        self.token_size = embed_dim
        self.downsample_feature_grid_factor = downsample_feature_grid_factor
        self.use_global_img = use_global_img

        self.image_encoder = AutoModel.from_pretrained(variant)
        hidden_size = self.image_encoder.config.hidden_size
        self.adapter = nn.Sequential(
            nn.LayerNorm(hidden_size),
            nn.Linear(hidden_size, embed_dim),
        )
        self.temporal_encoding = nn.Parameter(0.02 * torch.randn(1, self.num_frames, 1, 1, embed_dim))
        self.camera_encoding = nn.Parameter(0.02 * torch.randn(1, 1, self.num_cameras, 1, embed_dim))
        self.motion_token_encoder = MotionTokenEncoder(embed_dim, num_motion_tokens=num_motion_tokens)
        self.motion_type_embedding = nn.Parameter(torch.zeros(1, 1, embed_dim))
        self.motion_position_embedding = nn.Parameter(0.02 * torch.randn(1, num_motion_tokens, embed_dim))
        self.motion_scale = nn.Parameter(torch.tensor(1.0))

        if freeze:
            for p in self.image_encoder.parameters():
                p.requires_grad = False

    def _encode_frames(self, pixel_values: torch.Tensor, num_frames: int, num_cams: int) -> torch.Tensor:
        bs, _, _, num_patches, channels, height, width = pixel_values.shape
        if num_patches != 1:
            raise ValueError(f"DINOv2 expects num_patches=1, got {num_patches}")

        flat = pixel_values.reshape(bs * num_frames * num_cams, channels, height, width)
        with torch.no_grad():
            try:
                outputs = self.image_encoder(pixel_values=flat, interpolate_pos_encoding=True)
            except TypeError:
                outputs = self.image_encoder(pixel_values=flat)
            tokens = outputs.last_hidden_state[:, 1:]  # drop CLS token

        patch_size = int(getattr(self.image_encoder.config, "patch_size", 14))
        grid_h = height // patch_size
        grid_w = width // patch_size
        if tokens.shape[1] != grid_h * grid_w:
            raise ValueError(
                f"Unexpected DINO token count {tokens.shape[1]} for grid {grid_h}x{grid_w}"
            )

        tokens = tokens.view(bs * num_frames * num_cams, grid_h, grid_w, tokens.shape[-1])
        if self.downsample_feature_grid_factor is not None:
            factor = self.downsample_feature_grid_factor
            tokens = F.avg_pool2d(tokens.permute(0, 3, 1, 2), factor).permute(0, 2, 3, 1)

        tokens = self.adapter(tokens)
        tokens = tokens.flatten(1, 2)
        return tokens.view(bs, num_frames, num_cams, tokens.shape[-2], tokens.shape[-1])

    def forward(
        self,
        pixel_values: torch.Tensor,
        image_sizes=None,
        use_temporal_encoding: bool = True,
        use_positional_encoding: bool = True,
        use_camera_encoding: bool = True,
    ):
        bs, num_frames, num_cams, num_patches, channels, height, width = pixel_values.shape

        if num_frames >= 2:
            with torch.no_grad():
                feat_prev = self._encode_frames(pixel_values[:, :-1], num_frames - 1, num_cams)
                feat_prev = feat_prev[:, -1]

            feat_curr = self._encode_frames(pixel_values[:, -1:], 1, num_cams)
            feat_curr_sq = feat_curr[:, 0]

            diff = feat_curr_sq - feat_prev
            motion_tokens = self.motion_token_encoder(diff)
            motion_tokens = (
                self.motion_scale * motion_tokens
                + self.motion_type_embedding
                + self.motion_position_embedding
            )
            patch_embeddings = feat_curr_sq.unsqueeze(1)
            out_frames = 1
        else:
            patch_embeddings = self._encode_frames(pixel_values, num_frames, num_cams)
            motion_tokens = None
            out_frames = num_frames

        input_sequence = patch_embeddings
        _, _, _, n_tokens, channels = input_sequence.shape

        if use_temporal_encoding:
            input_sequence = input_sequence + self.temporal_encoding[:, :out_frames]
        if use_camera_encoding:
            input_sequence = input_sequence + self.camera_encoding

        embeds = input_sequence.view(bs, -1, channels)
        return embeds, (out_frames, n_tokens, channels), motion_tokens
