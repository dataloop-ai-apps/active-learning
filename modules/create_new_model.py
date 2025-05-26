import logging
import dtlpy as dl

logger = logging.getLogger('[ModelCreator]')


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
        print(f"train subset: {train_subset}")
        print(f"validation subset: {validation_subset}")
        print(f"model config: {model_configuration}")
    
        pipeline = context.pipeline
        pipeline_variables_dict = {var['name']: var for var in pipeline.variables}

        _model_configuration = base_model.configuration
            if isinstance(model_configuration, dict) and len(model_configuration) > 0:
                for config_name, config_val in model_configuration.items():
                    _model_configuration[config_name] = config_val
            pipeline_variables_dict['model_configuration'].value = _model_configuration

        logger.info(f'Creating new model from {base_model.name}.')

        node = context.node
        input_name = node.metadata['customNodeConfig']['modelName']
        # input_name = "{base_model.name}_{datetime.datetime.now().strftime('%Y_%m_%d-T%H_%M_%S')}"  # debug
        new_name = input_name
        while '{' in new_name:
            name_start, name_end = new_name.split('{', 1)
            executable_name, name_end = name_end.split('}', 1)
            exec_var = eval(executable_name)
            new_name = name_start + exec_var + name_end

        new_dataset = dataset if dataset else base_model.dataset
        new_project = new_dataset.project

        # get the train and validation subsets from the base model if they are not given
        train_filter = dl.Filters(custom_filter=train_subset)
        validation_filter = dl.Filters(custom_filter=validation_subset)
        if len(train_subset) == 0:
            train_filter = None
        if len(validation_subset) == 0:
            validation_filter = None

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
                    status='created',
                )
                break
            except dl.exceptions.BadRequest:
                new_name = f'{new_name}_v{i}'
                i += 1

        logger.info(f'New model {new_model.name} created from {base_model.name}.')
        return new_model, base_model
