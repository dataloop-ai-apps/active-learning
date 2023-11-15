import logging
import typing
import dtlpy as dl

predictor = dl.AppModule(name='Predict Items',
                         description='Predict batch of items. Optional update of the model version in the function.')

logger = logging.getLogger('ModelAdapter')


@predictor.set_init()
def predictor_init():
    logging.info("Initializing model prediction service.")
    predictor.adapter = None
    predictor.model_entity = None


def load_model(model_entity: dl.Model):
    adapter = model_entity.package.build(module_name='model-adapter',
                                         init_inputs={'model_entity': model_entity})
    return adapter


@predictor.add_function(display_name='Predict Items',
                        outputs={'items': 'Item[]',
                                 'annotations': 'Annotation[]'})
def predict_items(items: typing.List[dl.Item], model: dl.Model = None):
    """
    Run the predict function on the input list of items (or single) and return the items and the predictions.
    Each prediction is by the model output type (package.output_type) and model_info in the metadata

    :param items: `List[dl.Item]` list of items to predict
    :param model: `dl.Model` Model entity, if model is changed, the new model will be loaded before prediction

    :return: `List[dl.Item]`, `List[List[dl.Annotation]]`
    """
    if predictor.adapter is None or model.id != predictor.model_entity.id:
        predictor.adapter = load_model(model_entity=model)
        predictor.model_entity = model
        if model.id != predictor.model_entity.id:
            logger.info(f'Received a new model: name: {model.name}, id: {model.id}, '
                        f'replacing old one: name: {predictor.model_entity.name}, id: {predictor.model_entity.id}...')
        logger.info(f'Model loaded and ready to predict.')

    #######################
    # load configurations #
    #######################
    upload_annotations = predictor.model_entity.configuration.get('upload_annotations', True)
    conf_threshold = predictor.model_entity.configuration.get('conf_threshold', 0.1)
    batch_size = predictor.model_entity.configuration.get('batch_size', 16)

    items, annotations = predictor.adapter.predict_items(items=items,
                                                         upload_annotations=upload_annotations,
                                                         conf_threshold=conf_threshold,
                                                         batch_size=batch_size)

    return items, annotations
