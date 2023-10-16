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
   dpk = dl.dpks.get(dpk_name='active-learning-1.3')
   project.apps.install(dpk=dpk)
   ```

3. Go to “Pipelines” and “Create new pipeline”

4. Select the “Active Learning” template
5. Fill in the required inputs and outputs in each node
6. Start pipeline

To customize your pipeline, select the nodes from the

---

## Introduction

Dataloop pipelines provides a user-friendly interface for building, managing, and monitoring end-to-end machine learning
workflows. This Active Learning app installs custom nodes into Dataloop pipelines to allow users to implement active
learning pipelines in production.

Custom nodes installed include:

- data splitting
- create new models (for fine-tuning)
- compare two models

Each node is explained in detail below.


---

## Data Split Node

<img src="assets/data_split.png">

### Description

The **Data Split** node allows users to split data into groups, split equally or by percentage. This node takes a stream
of data and automatically assigns them to a data group based on user-defined groups and distribution. For example, if
you wanted a 80-20 split for model training, you would create two groups with the names and distributions of “train”

### App Usage in the Dataloop Platform

To use the Data Split node in Pipelines, use the following steps:

* Navigate to the Pipeline editor .
* Drag and drop the Data Split node to the canvas.
* Name each group and define the distribution (equal or custom).
* Connect the node to the next node.
* Run the pipeline.

---

## Create New Model Node

The **Create New Model** node takes an existing model and clones it with a defined dataset, training and validation
subset, and model configurations. This node outputs a model that is prepared for training.
The name of the new model entity is taken from the text box in the pipelines panel. If a model already exists with the
same name, a number will be automatically added as a suffix.

**Parameters**

- `base_model` - the model to clone (dl.Model)
- `dataset` - the dataset to train on (dl.Dataset)
- `train_subset` - the DQL query for the subset of training items (JSON)
- `validation_subset` - the DQL query for the subset of validation items (JSON)
- `model_configuration` - the model configurations to use for training (JSON)

**Outputs/returns**

- `new_model` - the new model entity created (dl.Model)

---

## Compare Model Node

The **Compare Models** node compares two models: a previously trained model, and the newly trained model. 
Comparisons are highly customizable and can also be done via the Dataloop SDK model adapters.

The default Dataloop compare model node can compare any two models that have either:

1) uploaded metrics to model management during model training, or
2) been evaluated on a common test subset.

To do the comparison, a `compare_config` JSON must be provided. The following keys are supported (with the indicated
defaults):

- `"wins"` - the metric to compare (string or float), i.e. `"any"`, `"all"`, or `"0.7"` to indicate 70% of the
  individual sub-comparisons need to result in a win in order for the overall comparison to be a win
- `"checks"` - a list of sub-comparisons to perform (list of dictionaries)
- `"verbose"` - whether to print the results of each sub-comparison (boolean), i.e. `true` or `false`

`"checks"` is where the user can list the specific metrics to be compared. The format of each check will depend on the
metric type.


If comparing model training metrics as described in **1)** above, the following subkeys are supported:

- `"type"` : the type of metric to compare (string), e.g. `"plot"`
- `"legend"` : the type of metric, e.g. `"loss"`
- `"figure"` : the title of the figure to compare, e.g. `"training loss"`
- `"x-index"` : the x-axis index of the metric to compare, e.g. `-1` for the final epoch, if `x` is epoch
- `"maximize"` : whether to maximize the metric (boolean), e.g. `false` for loss
- `"min_delta"` : the minimum delta to consider a comparison win (float), e.g. `0.1`


If comparing model predictions as described in **2)** above, the following subkeys are supported:

- `"wins"` - the metric to compare (string or float), i.e. `"any"`, `"all"`, or `"0.7"` to indicate 70% of the
  individual sub-comparisons need to result in a win in order for the overall comparison to be a win


**Parameters**

- `previous_model` - the previously trained model (dl.Model)
- `new_model` - the newly trained model to compare with the previous (dl.Model)
- `compare_config` - the configurations for the comparison (JSON)


**Outputs/returns**

- `winning_model` - the model that wins the comparison, with two "action" fields: `update_model` and `discard` (
  dl.Model)

---

## Contributions, Bugs and Issues - How to Contribute

We welcome anyone to help us improve this app.  
[Here's](CONTRIBUTING.md) a detailed instructions to help you open a bug or ask for a feature request