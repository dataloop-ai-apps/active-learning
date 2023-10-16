# Active Learning

Active learning is a subset of supervised learning that involves selecting the most informative data points for the model to train on. In active learning pipelines, the model is initially trained on a small labeled dataset, and then it selects the most informative examples from an unlabeled pool for a human expert to label. The model is then retrained on the newly labeled data, and the process repeats until the model achieves a satisfactory level of performance.

![Active Learning Pipeline](../../assets/active-learning-pipeline.png)


---
# Data Split Node

![Screenshot of data split node in pipelines](../../assets/data_split.png)

---
## Description

The Data Split application enables developers to split data into multiple groups. The data can be split equally or by a percentage.

## Setup
* In order to continue, you need to install our &nbsp;🚀 &nbsp;[Python SDK](https://github.com/dataloop-ai/dtlpy) and use our [CLI](https://sdk-docs.dataloop.ai/en/latest/cli.html).

## Installation
* Clone the repository -  `git clone https://github.com/dataloop-ai-apps/data-split.git`
* Navigate to the repository - `cd data-split`
* Publish the app -  `dlp app publish --project-name <PROJECT_NAME>`
* Install - `dlp app install --dpk-id <DPK ID> --project-name <PROJECT_NAME>`
Note: after installing the app, you can find it in the Dataloop Platform under the Apps tab.
and you can find a new node in the pipeline editor under Data tag.

## Application Usage in the Dataloop Platform
To use the Data Split in Pipeline, use the following steps:
* Navigate to the Pipeline editor .
* Drag and drop the Data Split node to the canvas.
* setup your groups.
* Connect the node to the next node.
* Run the pipeline.


### State structure

The following structure is saved upon the node's metadata.

```typescript
interface INodeConfigJSON {
    name: string
    distributeEqually: boolean
    groups: Group[]
    itemMetadata?: boolean
    validation: ValidationDescriptor
    ports?: Port[]
}
```

### Fields

`name`: A string value representing the name of the node.

`distributeEqually`: A boolean value indicating whether or not the data should be distributed equally between the groups.

`groups`: An array of objects representing the groups - each group has a name and a distribution percentage.

`itemMetadata`: A boolean that when set to true it add the action to the item metadata

`validation`: An object representing the validation information for the node.

`ports`: An array of objects representing the ports of the node.

### Example

Here are examples of what could be saved in the node's metadata under the `customNodeConfig` property, using the `updateNodeConfig` event.

```json
{
    "name": "Data",
    "distributeEqually": true,
    "groups": [
        {
            "id": "81fd5094-14ae-45a6-b301-dfc041085e3c",
            "name": "Group_1",
            "distribution": 33.33
        },
        {
            "id": "c609c463-4436-4354-90b1-e4d957b668da",
            "name": "Group_2",
            "distribution": 33.33
        },
        {
            "id": "e0308338-d309-4848-ae62-09790f638c01",
            "name": "Group_3",
            "distribution": 33.34
        }
    ],
    "itemMetadata": false,
    "validation": {
        "valid": true,
        "errors": []
    },
    "ports": [
        {
            "action": "Group_1",
            "name": "item",
            "type": "Item",
            "portPercentage": 33.33
        },
        {
            "action": "Group_2",
            "name": "item",
            "type": "Item",
            "portPercentage": 33.33
        },
        {
            "action": "Group_3",
            "name": "item",
            "type": "Item",
            "portPercentage": 33.34
        }
    ]
}
```

```json
{
    "name": "",
    "distributeEqually": true,
    "groups": [
        {
            "id": "81fd5094-14ae-45a6-b301-dfc041085e3c",
            "name": "Group_1",
            "distribution": 33.33
        },
        {
            "id": "c609c463-4436-4354-90b1-e4d957b668da",
            "name": "Group_2",
            "distribution": 33.33
        },
        {
            "id": "e4a93d13-de62-4bdd-9cd2-f36cc9029f5b",
            "name": "Group_3",
            "distribution": 33.34
        }
    ],
    "itemMetadata": false,
    "validation": {
        "valid": false,
        "errors": [
            {
                "message": "Node name error",
                "suggestion": "Please adjust the node name"
            },
            {
                "message": "Metadata key error",
                "suggestion": "Please adjust the metadata key"
            }
        ]
    },
    "ports": [
        {
            "action": "Group_1",
            "name": "item",
            "type": "Item",
            "portPercentage": 33.33
        },
        {
            "action": "Group_2",
            "name": "item",
            "type": "Item",
            "portPercentage": 33.33
        },
        {
            "action": "Group_3",
            "name": "item",
            "type": "Item",
            "portPercentage": 33.34
        }
    ]
}
```

## Contributions, Bugs and Issues - How to Contribute  
We welcome anyone to help us improve this app.  
[Here's](CONTRIBUTING.md) a detailed instructions to help you open a bug or ask for a feature request