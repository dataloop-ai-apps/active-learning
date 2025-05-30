import datetime
import logging
import dtlpy as dl

logger = logging.getLogger("[ModelCreator]")


class ModelCreator(dl.BaseServiceRunner):
    def __init__(self):
        pass

    @staticmethod
    def create_new_model(
        base_model: dl.Model,
        dataset: dl.Dataset,
        train_subset: dict,
        validation_subset: dict,
        model_configuration: dict,
        context: dl.Context,
    ):
        """
        Create a new model version from the input model

        :param base_model: model that will be used as a base for the new model.
        :param dataset: dataset that will be used for training the new model.
        :param train_subset: JSON for the DQL filter to get the train items from the given dataset
        :param validation_subset: JSON for the DQL filter to get the validation items from the given dataset
        :param model_configuration: JSON for model configurations (default is from the original model)
        :param context: IDs and other entities related to the item
        :return: new_model (dl.Model), a clone of the base model with the specified parameters.
        """
        if base_model is None:
            raise ValueError("Base model is required.")
        if dataset is None:
            raise ValueError("Dataset is required.")

        try:
            pipeline = context.pipeline
            pipeline_variables_dict = {var.name: var for var in pipeline.variables}
        except Exception:
            pipeline_variables_dict = {"train_subset": train_subset, "validation_subset": validation_subset, "model_configuration": model_configuration}

        _model_configuration = base_model.configuration
        if isinstance(model_configuration, dict) and len(model_configuration) > 0:
            for config_name, config_val in model_configuration.items():
                _model_configuration[config_name] = config_val
            pipeline_variables_dict["model_configuration"] = _model_configuration

        logger.info(f"Creating new model from {base_model.name}.")

        node = context.node
        try:
            input_name = node.metadata['customNodeConfig']['modelName']
        except Exception:
            input_name = f"{base_model.name}_{datetime.datetime.now().strftime('%Y_%m_%d-T%H_%M_%S')}"
        new_name = input_name
        while "{" in new_name:
            name_start, name_end = new_name.split("{", 1)
            executable_name, name_end = name_end.split("}", 1)
            try:
                exec_var = eval(executable_name) if executable_name else ""
            except Exception:
                logger.error(f"Error evaluating executable name: {executable_name}.")
                exec_var = ""
            new_name = name_start + exec_var + name_end
        new_dataset = dataset if dataset else base_model.dataset
        new_project = new_dataset.project

        if train_subset is None or len(train_subset) == 0:
            # get the train subset from the base model
            base_train_subset = base_model.metadata.get("system", {}).get("subsets", {}).get("train", {})
            pipeline_variables_dict["train_subset"] = base_train_subset

        if validation_subset is None or len(validation_subset) == 0:
            # get the validation subset from the base model
            base_validation_subset = base_model.metadata.get("system", {}).get("subsets", {}).get("validation", {})
            pipeline_variables_dict["validation_subset"] = base_validation_subset

        # update back to pipeline variables
        try:
            context.pipeline.variables = pipeline_variables_dict
        except Exception:
            pass

        train_filter = dl.Filters(custom_filter=train_subset)
        validation_filter = dl.Filters(custom_filter=validation_subset)
        # try creating model clone with the given name, if it fails, add a number to the end of the name and try again
        i = 1
        new_model = None
        while new_model is None:
            try:
                new_model = base_model.clone(
                    model_name=new_name,
                    project_id=new_project.id,
                    dataset=new_dataset,
                    configuration=_model_configuration,
                    train_filter=train_filter,
                    validation_filter=validation_filter,
                    status="created",
                )
                break
            except dl.exceptions.BadRequest:
                new_name = f"{new_name}_v{i}"
                i += 1

        logger.info(f"New model {new_model.name} created from {base_model.name}.")
        return new_model, base_model
