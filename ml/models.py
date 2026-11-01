from __future__ import annotations

import torch.nn as nn
from torchvision import models

SUPPORTED = ("efficientnet_b0", "efficientnet_b3", "efficientnet_b4", "resnet50")


def build_model(
    arch: str, num_classes: int, pretrained: bool = True, dropout: float = 0.3
) -> nn.Module:
    if arch not in SUPPORTED:
        raise ValueError(f"Unsupported architecture {arch!r}; choose one of {SUPPORTED}.")
    if num_classes < 1:
        raise ValueError("num_classes must be a positive integer.")
    if not 0.0 <= dropout < 1.0:
        raise ValueError("dropout must be in the range [0, 1).")

    weights = models.get_model_weights(arch).DEFAULT if pretrained else None
    model = models.get_model(arch, weights=weights)
    if arch.startswith("efficientnet"):
        in_features = model.classifier[1].in_features
        model.classifier = nn.Sequential(nn.Dropout(dropout), nn.Linear(in_features, num_classes))
    else:
        in_features = model.fc.in_features
        model.fc = nn.Sequential(nn.Dropout(dropout), nn.Linear(in_features, num_classes))
    return model


def head_module(model: nn.Module) -> nn.Module:
    """Return the classifier head for supported torchvision model families."""
    if hasattr(model, "classifier"):
        return model.classifier
    if hasattr(model, "fc"):
        return model.fc
    raise ValueError(f"Cannot find a classifier head on {type(model).__name__}.")


def set_backbone_trainable(model: nn.Module, trainable: bool) -> None:
    head_parameters = {id(parameter) for parameter in head_module(model).parameters()}
    for parameter in model.parameters():
        parameter.requires_grad = id(parameter) in head_parameters or trainable


def gradcam_layer(model: nn.Module, arch: str) -> nn.Module:
    """Return the final convolutional feature block used by the inference Grad-CAM."""
    if arch not in SUPPORTED:
        raise ValueError(f"Unsupported architecture {arch!r}; choose one of {SUPPORTED}.")
    if arch.startswith("efficientnet"):
        return model.features[-1]
    return model.layer4[-1]
