import numpy as np
import torch
from torch import nn
from transformers import LlavaNextProcessor

from simlingo_base_training.models.encoder.llavanext_model import LingoLlavaNextModel


class MotionTokenEncoder(nn.Module):
    def __init__(self, embed_dim: int, num_motion_tokens: int = 8):
        super().__init__()
        self.num_motion_tokens = num_motion_tokens
        self.encoder = nn.Sequential(
            nn.LayerNorm(embed_dim),
            nn.Linear(embed_dim, embed_dim // 4),
            nn.SiLU(),
            nn.Linear(embed_dim // 4, embed_dim),
        )

    def forward(self, diff: torch.Tensor) -> torch.Tensor:
        BS, num_cams, n_tokens, channels = diff.shape
        motion = self.encoder(diff)
        motion = motion.view(BS, num_cams * n_tokens, channels).transpose(1, 2)
        motion = nn.functional.adaptive_avg_pool1d(motion, self.num_motion_tokens)
        return motion.transpose(1, 2)


class LLaVAnextEncoderModel(nn.Module):
    def __init__(self,
        variant: str,
        embed_dim: int,
        freeze: True,
        downsample_feature_grid_factor: int = 2,
        use_global_img = False,
    ):
    
        super().__init__()
        self.num_cameras = 1
        self.num_frames = 1
        self.token_size = embed_dim

        self.downsample_feature_grid_factor = downsample_feature_grid_factor

        self.image_encoder = LingoLlavaNextModel.from_pretrained(variant)
        self.image_encoder.use_global_img = use_global_img
        self.image_encoder.config.image_grid_pinpoints = [[336,672]] # this is done to save memory otherwise it would use higehr res input dependen on how we cut the image
        self.image_encoder.language_model = None
        print("\033[91m" + "Using LLaVA pretraining for the image encoder" + "\033[0m")
        
        self.projection = nn.Linear(self.image_encoder.base_model.config.vision_config.intermediate_size, embed_dim)
        # Embeddings: BS, N_FRAMES, N_CAMS, N_PATCHES, EMBED_DIM
        self.temporal_encoding = nn.Parameter(0.02 * torch.randn(1, self.num_frames, 1, 1, embed_dim))
        self.camera_encoding = nn.Parameter(0.02 * torch.randn(1, 1, self.num_cameras, 1, embed_dim))
        self.motion_token_encoder = MotionTokenEncoder(embed_dim, num_motion_tokens=8)
        self.motion_type_embedding = nn.Parameter(torch.zeros(1, 1, embed_dim))
        self.motion_position_embedding = nn.Parameter(0.02 * torch.randn(1, 8, embed_dim))
        self.motion_scale = nn.Parameter(torch.tensor(1.0))

        # freeze the paramaeters -> no gradient updates
        if freeze:
            for p in self.parameters():
                p.requires_grad = False

            # activate the projection layer
            self.projection.weight.requires_grad = True
            self.projection.bias.requires_grad = True
            self.temporal_encoding.requires_grad = True
            self.camera_encoding.requires_grad = True
            # Motion tokens are always trainable.
            for p in self.motion_token_encoder.parameters():
                p.requires_grad = True
            self.motion_type_embedding.requires_grad = True
            self.motion_position_embedding.requires_grad = True
            self.motion_scale.requires_grad = True

    def _encode_frames(self, pixel_values: torch.Tensor, image_sizes, num_frames: int, num_cams: int) -> torch.Tensor:
        """Encode pixel_values and project. Returns [BS, num_frames, num_cams, N_tokens, D]."""
        BS = pixel_values.shape[0]
        raw = self.image_encoder.forward_image(
            pixel_values=pixel_values,
            image_sizes=image_sizes,
            downsample_feature_grid_factor=self.downsample_feature_grid_factor,
        )
        proj = self.projection(raw)
        return proj.view(BS, num_frames, num_cams, proj.shape[-2], proj.shape[-1])

    def forward(
        self,
        pixel_values: torch.Tensor,
        image_sizes = None,
        use_temporal_encoding: bool = True,
        use_positional_encoding: bool = True,
        use_camera_encoding: bool = True,
    ) -> torch.Tensor:

        BS, num_frames, num_cams, num_patches, C, H, W = pixel_values.shape

        if num_frames >= 2:
            # Split image_sizes: [BS*num_frames*num_cams, 2] → by frame
            if image_sizes is not None:
                sizes_4d = image_sizes.view(BS, num_frames, num_cams, 2)
                prev_sizes = sizes_4d[:, :-1].reshape(BS * (num_frames - 1) * num_cams, 2)
                curr_sizes = sizes_4d[:, -1:].reshape(BS * num_cams, 2)
            else:
                prev_sizes = curr_sizes = None

            # Encode prev frame(s) without gradient
            with torch.no_grad():
                feat_prev = self._encode_frames(
                    pixel_values[:, :-1], prev_sizes, num_frames - 1, num_cams
                )  # [BS, num_frames-1, num_cams, N, D]
                feat_prev = feat_prev[:, -1]  # use last prev frame: [BS, num_cams, N, D]

            # Encode current frame normally
            feat_curr = self._encode_frames(
                pixel_values[:, -1:], curr_sizes, 1, num_cams
            )  # [BS, 1, num_cams, N, D]
            feat_curr_sq = feat_curr[:, 0]  # [BS, num_cams, N, D]

            diff = feat_curr_sq - feat_prev  # [BS, num_cams, N, D]
            motion_tokens = self.motion_token_encoder(diff)  # [BS, K, D]
            motion_tokens = (
                self.motion_scale * motion_tokens
                + self.motion_type_embedding
                + self.motion_position_embedding
            )

            # Reshape to [BS, 1, num_cams, N, D] for downstream compatibility
            patch_embeddings = feat_curr_sq.unsqueeze(1)
            out_frames = 1
        else:
            patch_embeddings = self._encode_frames(pixel_values, image_sizes, num_frames, num_cams)
            motion_tokens = None
            out_frames = num_frames

        input_sequence = patch_embeddings
        _, _, _, n_tokens, channels = input_sequence.shape

        if use_temporal_encoding:
            input_sequence = input_sequence + self.temporal_encoding[:, :out_frames]
        if use_camera_encoding:
            input_sequence = input_sequence + self.camera_encoding

        embeds = input_sequence.view(BS, -1, channels)
        return embeds, (out_frames, n_tokens, channels), motion_tokens



if __name__ == "__main__":
    model = LLaVAnextEncoderModel(
        variant="llava-hf/llava-v1.6-mistral-7b-hf",
        debug=True,
        embed_dim=256,
        freeze=True,
    )
    processor = LlavaNextProcessor.from_pretrained("llava-hf/llava-v1.6-mistral-7b-hf")

    # BS, N_FRAMES, N_CAMS, 3, H, W
    # random vector between 0 and 1
    image = np.random.rand(2, 4, 2, 3, 512, 1024).astype(np.float32)
    image = torch.tensor(image)

    # merge BS and N_FRAMES and N_CAMS
    image = image.view(-1, 3, 512, 1024)

    inputs = processor.image_processor(image, return_tensors="pt").to("cuda:0")
     # typing.Union[ForwardRef('PIL.Image.Image'), numpy.ndarray, ForwardRef('torch.Tensor'), typing.List[ForwardRef('PIL.Image.Image')], typing.List[numpy.ndarray], typing.List[ForwardRef('torch.Tensor')]]

    output = model(**inputs)
    print(output[0].shape, output[1])

    # output_image_shape = True
    # output = model(image, output_image_shape)
    # print(output.shape)
