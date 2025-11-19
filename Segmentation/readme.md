# Segmentation Experiments

This folder contains experiments demonstrating **three types of image segmentation** using PyTorch and Detectron2:  

1. **Semantic Segmentation** – classifies each pixel into a category.  
2. **Instance Segmentation** – detects and segments individual objects.  
3. **Panoptic Segmentation** – combines semantic and instance segmentation for complete scene understanding.  

---

## Setup

Install required libraries:

```bash
!pip install torch torchvision matplotlib opencv-python
!pip install 'git+https://github.com/facebookresearch/detectron2.git'
```

## Folder Contents
- semantic_segmentation.ipynb — Using DeepLabV3 for semantic segmentation.

- instance_segmentation.ipynb — Using Mask R-CNN for instance segmentation.

- panoptic_segmentation.ipynb — Using Detectron2 Panoptic FPN for panoptic segmentation.

# 1. Semantic Segmentation (DeepLabV3)
- Goal: Assign a class label to every pixel in the image.

- Model: DeepLabV3-ResNet50 pretrained on COCO.

- Visualization: Shows the segmentation mask over the original image.
```
semantic_model = models.segmentation.deeplabv3_resnet50(pretrained=True)
```
# 2. Instance Segmentation (Mask R-CNN)
- Goal: Detect and segment individual objects within the image.

- Model: Mask R-CNN pretrained on COCO.

- Visualization: Shows individual object masks overlaid on the original image.

- Filtering: Only predictions with confidence > 0.5 are displayed.

# 3. Panoptic Segmentation (Detectron2 Panoptic FPN)
- Goal: Combine semantic and instance segmentation for a full scene understanding.

- Model: Panoptic FPN pretrained on COCO Panoptic dataset.

- Visualization: Colored masks for all objects and regions in the image.

```
cfg = get_cfg()
cfg.merge_from_file(model_zoo.get_config_file("COCO-PanopticSegmentation/panoptic_fpn_R_50_3x.yaml"))
cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url("COCO-PanopticSegmentation/panoptic_fpn_R_50_3x.yaml")
```
# How to Run
Open the notebooks in Google Colab or a local environment with GPU support.

Ensure the sample image traffic.jpg is in the working directory.

Run each notebook sequentially to see segmentation results.

You can replace traffic.jpg with your own images for experimentation.

# Notes
These notebooks are experimental and meant for learning purposes.

GPU is recommended for faster inference, especially for Detectron2.

The experiments showcase different segmentation approaches and visualization techniques in Python.

Segmentation is a cornerstone of computer vision, enabling applications from autonomous driving to medical imaging. Experiment with different models, images, and parameters to understand their strengths and limitations.
