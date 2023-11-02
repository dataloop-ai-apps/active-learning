# Active Learning

Active learning is a method in machine learning that selects more informative data points to label, prioritizing those
that would provide the most valuable information. By selectively labeling only informative examples, active learning
helps improve learning process efficiency to achieve high accuracy with fewer labeled samples.

![alt text](assets/active-learning-pipeline.png)

---

## Quick Start

* In order to continue, you need to install our &nbsp;🚀 &nbsp;[Python SDK](https://github.com/dataloop-ai/dtlpy) and use
  our [CLI](https://sdk-docs.dataloop.ai/en/latest/cli.html).

1. Clone the repository
   ```
   git clone https://github.com/dataloop-ai-apps/active-learning.git
   ```

2. The app can be installed via terminal or python.

   In terminal, use the following commands:
   ```bash
   dlp app install --dpk-id <DPK ID> --project-name <PROJECT_NAME>
   ```

   In python, use the following commands:

   ```python
    import dtlpy as dl
    project = dl.projects.get(project_name='<project-name>')
    dpk = dl.dpks.get(dpk_name='<dpk-name>')
    project.apps.install(dpk=dpk.display_name)
   ```

3. Go to “Pipelines” and “Create new pipeline”
4. Select the “Active Learning” template
5. Fill in the required inputs and outputs in each node
6. Start pipeline

---

## Introduction

Dataloop pipelines provides a user-friendly interface for building, managing, and monitoring end-to-end machine learning
workflows. This Active Learning app installs custom nodes into Dataloop pipelines to allow users to implement active
learning pipelines in production.

Custom nodes installed include:

- model data split
- create new models
- compare two models

Each node is explained in detail below.

---

## Model Data Split Node

<img src="assets/data_split.png">

The **Model Data Split** node is a data processing tool that empowers you to split your data into subsets at runtime. Use this node to segment your ground truth into train, validation and test sets, simplifying the process.

Simply specify the desired subsets distribution, and the Data Split node will seamlessly assign each item to its respective subset using a metadata tags.

#### App Usage in the Dataloop Platform

To use the Data Split node in Pipelines, use the following steps:

* Navigate to the Pipeline editor .
* Drag and drop the Model Data Split node to the canvas.
* Define the distribution desired for each subset (equal or custom).
* Connect the node to the next node.

---

## Create New Model Node

The **Create New Model** node generates a new model version by cloning an existing model, making it ready for fine-tuning.

The node inputs can be provided using parameters (fixed values or dynamic variables) or through node connections.

Upon execution, the node will generate the new model as output. For more information, see our Active Learning documentation.


#### Parameters

- `base_model` - the model to clone (dl.Model)
- `dataset` - the dataset to train on (dl.Dataset)
- `train_subset` - the DQL query for the subset of training items ([JSON](pipeline_configs/train_subset_filter.json))
- `validation_subset` - the DQL query for the subset of validation items ([JSON](pipeline_configs/validation_subset_filter.json))
- `model_configuration` - the model configurations to use for training (JSON: Model Configuration from Model Management)

#### Outputs/returns

- `new_model` - the new model entity created `dl.Model`
- `base_model` - the base model entity used to clone existing model `dl.Model`

---

## Compare Models Node

The **Compare Models** node undertakes a comparison between two trained model versions based on their evaluation (same test set) or the model metrics created during the train process.

The New model input undergoes testing, and if it proves superior, it will be sent as an output labelled 'Update model', signifying deployment readiness. Alternatively, it will be labelled 'Discard'. For more information, see our Active Learning documentation

#### Parameters

- `previous_model` - the previously trained model `dl.Model`
- `new_model` - the newly trained model to compare with the previous `dl.Model`
- `compare_config` - the configurations for the comparison ([JSON](pipeline_configs/compare_configurations.json))
- `dataset` - the dataset the models were evaluated on `dl.Dataset`

#### Compare configs:

The compare configurations a dictionary with 2 sub-dicts:

- checks: includes sub-dicts the metrics that the models will be compared by, currently only `precision-recall` is supported.
          need to define `iou_threshold` and `min_delta` for the metric comparison.
- `"wins"` : the metric to compare (string or float), i.e. `"any"`, `"all"`, or `"0.7"` to indicate 70% of the
  individual sub-comparisons need to result in a win in order for the overall comparison to be a win.
  `wins` is used when comparing annotation scored.

if no checks are provided, the comparison will be done by the model evaluation metrics, based on the annotation scores,
based on the win configurations.


#### Outputs/returns

- `winning_model` - `dl.Model` - the model that wins the comparison, with two "action" fields: `update_model` and `discard`
---

## Contributions, Bugs and Issues - How to Contribute

We welcome anyone to help us improve this app.  
[Here's](CONTRIBUTING.md) a detailed instructions to help you open a bug or ask for a feature request