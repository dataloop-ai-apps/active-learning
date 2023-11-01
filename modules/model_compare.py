import dtlpy as dl
import numpy as np
import pandas as pd
import logging
from dtlpymetrics.models.image import get_model_scores_df
from dtlpymetrics import precision_recall
from sklearn.metrics import auc

comparator = dl.AppModule(name='compare_models',
                          description='Compares two models in relation to a user-specified.'
                                      'metric and attaches a "win" or "lose" action filter.')

logger = logging.getLogger('ModelCompare')
logger.setLevel(logging.INFO)


@comparator.set_init()
def setup():
    pass


def metrics_to_df(model: dl.Model) -> pd.DataFrame:
    """
    Converts the metrics of a model to extract x and y to columns.
    :param model: model entity from which to download metrics
    :return:
    """
    samples = model.metrics.list().to_df()

    try:
        data = samples['data'].values
        x = [d['x'] for d in data]
        y = [d['y'] for d in data]
        samples['x'] = x
        samples['y'] = y
    except KeyError:
        logger.warning(f"Metrics for model {model.name} do not contain data. Please check model.")

    return samples


@comparator.add_function(display_name="Compare Models")
def compare_models(previous_model: dl.Model,
                   new_model: dl.Model,
                   compare_config: dict,
                   progress: dl.Progress,
                   context: dl.Context,
                   dataset: dl.Dataset = None,
                   ) -> dl.Model:
    """
    Compare metrics of two models to determine which is better.

    :param previous_model: previous model
    :param new_model: new model to compare against the original model
    :param compare_config: JSON indicating which variables are being compared
    :param dataset: optional dataset entity to be able to compare based on model evaluation in a previous node
    :param progress: event progress necessary for updated the "action" filter of subset assignment
    :param context: context of the function
    :return:
    """
    logger.info(f"Compare configuration: {compare_config}")

    if compare_config is None:
        compare_config = {}
    # TODO add comparison based on evaluation from previous nose
    if dataset is None:
        # compare by model training
        is_improved = compare_model_training(current_model_metrics=metrics_to_df(previous_model),
                                             new_model_metrics=metrics_to_df(new_model),
                                             configuration=compare_config)
    else:
        get_eval_df(previous_model=previous_model,
                    new_model=new_model,
                    compare_config=compare_config,
                    dataset=dataset)
        is_improved = compare_model_evaluation(configuration=compare_config)
    winning_model = new_model if is_improved else previous_model

    actions = ['update model', 'discard']
    if is_improved is True:
        progress.update(action=actions[0])
    else:
        progress.update(action=actions[1])

    add_item_metadata = context.node.metadata.get('customNodeConfig', {}).get('itemMetadata', False)
    if add_item_metadata:
        if 'system' not in winning_model.metadata:
            winning_model.metadata['system'] = {}
        if 'tags' not in winning_model.metadata['system']:
            winning_model.metadata['system']['tags'] = {}
        winning_model.metadata['system']['tags'][actions[0]] = True
        winning_model = winning_model.update(True)

    return winning_model


def get_eval_df(previous_model: dl.Model,
                new_model: dl.Model,
                compare_config: dict,
                dataset: dl.Dataset = None):
    """

    :param previous_model:
    :param new_model:
    :param compare_config:
    :param dataset:
    :return:
    """
    checks = compare_config.get('checks', dict())
    for metric_name, metric_config in checks.items():
        if metric_name == 'precision_recall':
            iou_threshold = metric_config.get('iou_threshold', 0.01)
            current_eval_df = precision_recall.calc_precision_recall(dataset_id=dataset.id,
                                                                     model_id=previous_model.id,
                                                                     iou_threshold=iou_threshold,
                                                                     method_type='every_point'
                                                                     )

            new_eval_df = precision_recall.calc_precision_recall(dataset_id=dataset.id,
                                                                 model_id=new_model.id,
                                                                 iou_threshold=iou_threshold,
                                                                 method_type='every_point')
            metric_config['current_model_metrics'] = current_eval_df
            metric_config['new_model_metrics'] = new_eval_df
        else:
            raise NotImplementedError(f"Metric {metric_name} is not implemented, use precision_recall instead.")
    if len(checks) == 0:
        current_model_metrics = get_model_scores_df(model=previous_model,
                                                    dataset=dataset)
        new_model_metrics = get_model_scores_df(model=new_model,
                                                dataset=dataset)

        common_ids = current_model_metrics.merge(new_model_metrics, on='item_id', how='inner')['item_id']
        current_model_metrics = current_model_metrics[current_model_metrics['item_id'].isin(common_ids)]
        new_model_metrics = new_model_metrics[new_model_metrics['item_id'].isin(common_ids)]
        checks['annotation_score'] = {'current_model_metrics': current_model_metrics,
                                      'new_model_metrics': new_model_metrics
                                      }


def compare_model_training(current_model_metrics: pd.DataFrame,
                           new_model_metrics: pd.DataFrame,
                           configuration: dict) -> bool:
    """

    :param current_model_metrics:
    :param new_model_metrics:
    :param configuration:
    :return: True is the new one is better
    """
    wins = configuration.get('wins', None)
    if wins is None:
        logger.warning("No wins specified in configuration. Using 'any' as default.")
        wins = 'any'
    checks = configuration.get('checks', [])
    verbose = configuration.get('verbose', False)
    # labels_filter = configuration.get('labels_filter', None) # TODO support filtering by specific labels
    new_model_wins = list()

    for check in checks:
        min_delta = check.get('min_delta', 0)
        maximize = check.get('maximize', True)
        figure = check.get('figure', None)
        legend = check.get('legend', None)
        x_index = check.get('x_index', None)
        x_value = check.get('x_value', None)
        # TODO do some sanity check here (if none, give default value and warn)

        # now we filter the current model Dataframe by column values
        current_values = current_model_metrics.loc[(current_model_metrics['figure'] == figure) &
                                                   (current_model_metrics['legend'] == legend)]
        current_x = current_values['x'].values
        current_y = current_values['y'].values

        if len(current_x) == 0 or len(current_y) == 0:
            raise ValueError(f"Could not find figure {figure} and legend {legend} in current model metrics")
        # TODO check the number of returned values and warn if there is more than one
        current_value = current_y[current_x == current_x[x_index]][0]

        # now we filter the new model Dataframe by column values
        new_values = new_model_metrics.loc[(new_model_metrics['figure'] == figure) &
                                           (new_model_metrics['legend'] == legend)]
        new_x = new_values['x'].values
        new_y = new_values['y'].values
        if len(new_x) == 0 or len(new_y) == 0:
            raise ValueError(f"Could not find figure {figure} and legend {legend} in current model metrics")
        # TODO check the number of returned values and warn if there is more than one
        new_value = new_y[new_x == new_x[x_index]][0]
        if maximize is True:
            win_check = (new_value > (current_value + min_delta))
        else:
            win_check = (new_value < (current_value - min_delta))
        new_model_wins.append(win_check)

        if verbose:
            logger.info(
                f'comparing: figure: {figure}, legend {legend}. maximize {maximize}, min_delta {min_delta}, current_value: {current_value}, new_value: {new_value}. new model won? {win_check}')

    # TODO check all config return types
    logger.info(f"finished comparing, wins list: {new_model_wins}")

    return check_check_if_winning(wins, new_model_wins)


def check_check_if_winning(wins, new_model_wins):
    if wins == 'all':
        is_winning = True if all(new_model_wins) else False
    elif wins == 'any':
        is_winning = True if any(new_model_wins) else False
    elif isinstance(wins, float):
        is_winning = True if (sum(new_model_wins) / len(new_model_wins)) > wins else False
    else:
        is_winning = False
    return is_winning


def compare_model_evaluation(configuration: dict) -> bool:
    """
    Compare two models based on their predictions on a dataset.

    :param configuration: JSON indicating which variables are being compared
    :return: bool indicating if the new model is better
    """

    # compare model scores for each *item*
    # each item's scores needs to calculated by dtlpymetrics
    # then we need to compare the scores for each item
    # decide on a winner according to any/all/percentage of items

    wins = configuration.get('wins', None)
    if wins is None:
        logger.warning("No wins specified in configuration. Using 'any' as default.")
        wins = 'any'
    checks = configuration.get('checks', [])

    # summarize scores by *item*
    # annotation scores are an average of all three: label, attribute, iou
    if len(checks) == 0:
        current_model_metrics = configuration.get('annotation_score').get('current_model_metrics')
        new_model_metrics = configuration.get('annotation_score').get('new_model_metrics')
        item_scores_old = current_model_metrics.groupby(['item_id'])['annotation_score'].mean()
        item_scores_new = new_model_metrics.groupby(['item_id'])['annotation_score'].mean()
        new_model_wins = np.array(item_scores_new > item_scores_old)
        is_improved = check_check_if_winning(wins, new_model_wins)
    else:
        is_improved = _compare(configuration=configuration)

    logger.warning(f"finished comparing, new model won : {is_improved}")

    return is_improved


def _compare(configuration: dict) -> bool:
    """
    Using two result.csv files received model management metrics,
    find which of them is improves performance.
    :param configuration: JSON indicating which variables are being compared
    :Keyword Arguments:

    ******* SPECIFIC METRIC *******

    * *precision* (``bool``) --
      compare models by *only* Precision metric [default: False]
    * *recall* (``bool``) --
      compare models by *only* Recall metric [default: False]
    * *f1* (``bool``) --
      compare models by *only* f1-measure metric [default: False]
    * *mAP50* (``bool``) --
      compare models by *only* mAP50 metric [default: False]
    * *mAP50_95* (``bool``) --
      compare models by *only* mAP50_95 metric [default: False]
    note: if any metric was not chosen, the calculation takes *everything*

    ******* SETTINGS *******

    * *soft_check* (``function``) --
      require custom comparison function between two columns [default: Python's builtin *any*]
    * *iou_threshold* (``list | float``) --
      perform comparison based on specific (single/boundaries) IoU value [default: everything]
    * *same_pre_model* (``bool``) --
      require that both models were trained from the same source [default: false]
    * *specific_label* (``list``) --
      perform comparison based on specific label [default: everything]
    * *min_delta* (``float``) --
      require minimum difference between the metrics before considering it as improvement [default: 0]
    * *lower_is_better_metrics* (``list``) --
      specify list of metrics which require *decrease* to represent improvement [default: 0]
    * *verbose* (``bool``) --
      stdout tabular information in runtime  [default: False]

    :return: True if the comparison detected any improvement OR equalization, else - False.
    """

    def __compare(_current: pd.DataFrame, _new: pd.DataFrame):
        # Sort the precision and recall values together.
        current_precision_np = np.asarray(_current['precision'])
        current_recall_np = np.asarray(_current['recall'])
        current_sorted_precision_recall = np.array([current_precision_np, current_recall_np]).T
        sorted_indices = current_sorted_precision_recall[:, 1].argsort()[::-1]
        current_sorted_precision_recall = current_sorted_precision_recall[sorted_indices]

        # Calculate the AUC-PR.
        current_auc_pr = auc(current_sorted_precision_recall[:, 1], current_sorted_precision_recall[:, 0])
        logger.info(f"current model auc pr: {current_auc_pr}")

        # Sort the precision and recall values together.
        new_precision_np = np.asarray(_new['precision'])
        new_recall_np = np.asarray(_new['recall'])
        new_sorted_precision_recall = np.array([new_precision_np, new_recall_np]).T
        sorted_indices = new_sorted_precision_recall[:, 1].argsort()[::-1]
        new_sorted_precision_recall = new_sorted_precision_recall[sorted_indices]

        # Calculate the AUC-PR.
        new_auc_pr = auc(new_sorted_precision_recall[:, 1], new_sorted_precision_recall[:, 0])
        logger.info(f"new model auc pr: {new_auc_pr}")

        return new_auc_pr > current_auc_pr

    def _filter(_current_metric: pd.DataFrame, _new_metric: pd.DataFrame, **kwargs):
        """
        concatenate filtering over the dataFrames before performing metrics comparison
        :param _previous_metric: previous metric table
        :param _current_metric: current metric table
        :param kwargs: filter options
        :return: filtered tables
        """

        def _range_query(table, col, rng):
            return table.loc[table[col].isin(rng)]

        # settings
        labels = kwargs.get("specific_label", None)

        # TODO rename to be able to filter by dataset labels
        # filters by a list of labels
        if labels is not None:
            _current_metric = _range_query(_current_metric, "label", labels)  # _p.loc[_p["label"].isin(labels)]
            _new_metric = _range_query(_new_metric, "label", labels)

        return _current_metric, _new_metric

    config_checks = configuration.get("checks", dict())
    result = False
    for metric_name, metric_config in config_checks.items():
        current_sheet = metric_config.get('current_model_metrics')
        new_sheet = metric_config.get('new_model_metrics')
        current_metric, new_metric = _filter(current_sheet,
                                             new_sheet,
                                             **metric_config)

        result = __compare(current_metric, new_metric)
    return result
