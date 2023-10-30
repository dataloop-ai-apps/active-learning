import dtlpy as dl
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('DataSplit')


class ServiceRunner(dl.BaseServiceRunner):

    def __init__(self):
        ...

    @staticmethod
    def data_split(item: dl.Item, progress: dl.Progress, context: dl.Context) -> dl.Item:
        """
        Split data into subsets (e.g. train, validation and test sets)

        :param item: item to be distributed into one of the subset groups
        :param progress: event progress necessary for updated the "action" filter of subset assignment
        :param context: entity IDs of related entities to the item
        :return:
        """

        node = context.node
        groups = node.metadata['customNodeConfig']['groups']
        population = [group['name'] for group in groups]
        distribution = [int(group['distribution']) for group in groups]
        action = random.choices(population=population, weights=distribution)
        progress.update(action=action[0])
        if action[0] == 'test':
            annotations = item.annotations.list()
            for annotation in annotations:
                if 'model' in annotation.metadata.get('user', dict()):
                    logger.info('removing model metadata from item annotations')
                    annotation.metadata['user'].pop('model')
                    annotation.update()
        add_item_metadata = context.node.metadata.get('customNodeConfig', {}).get('itemMetadata', False)
        if add_item_metadata:
            if 'system' not in item.metadata:
                item.metadata['system'] = {}
            if 'tags' not in item.metadata['system']:
                item.metadata['system']['tags'] = {}
            item.metadata['system']['tags'][action[0]] = True
            item = item.update(True)
        return item
