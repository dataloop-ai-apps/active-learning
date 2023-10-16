import dtlpy as dl
import numpy as np
import pandas as pd
import logging
from dtlpymetrics.models.image import get_model_scores_df

comparator = dl.AppModule(name='compare_models',
                          description='Compares two models in relation to a user-specified.'
                                      'metric and attaches a "win" or "lose" action filter.')

logger = logging.getLogger('ModelAdapter')
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
        current_eval_df = get_model_scores_df(dataset=dataset, model=previous_model)
        new_eval_df = get_model_scores_df(dataset=dataset, model=new_model)

        is_improved = compare_model_evaluation(current_model_metrics=current_eval_df,
                                               new_model_metrics=new_eval_df,
                                               configuration=compare_config)
        # score_types=[ScoreType.ANNOTATION_IOU,
        #              ScoreType.ANNOTATION_ATTRIBUTE,
        #              ScoreType.ANNOTATION_LABEL])

    winning_model = new_model if is_improved else previous_model
    losing_model = previous_model if is_improved else new_model

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


def compare_model_evaluation(current_model_metrics: pd.DataFrame,
                             new_model_metrics: pd.DataFrame,
                             configuration: dict) -> bool:
    """
    Compare two models based on their predictions on a dataset.

    :param current_model_metrics: pd.DataFrame of scores for the current model predictions on a dataset
    :param new_model_metrics:  pd.DataFrame of scores for the new model predictions on a dataset
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
    item_scores_old = current_model_metrics.groupby(['item_id'])['annotation_score'].mean()
    item_scores_new = new_model_metrics.groupby(['item_id'])['annotation_score'].mean()
    new_model_wins = np.array(item_scores_new > item_scores_old)

    logger.warning(f"finished comparing, wins list: {new_model_wins}")

    return check_check_if_winning(wins, new_model_wins)


def compare2(previous_model_metrics: pd.DataFrame,
             current_model_metrics: pd.DataFrame,
             configuration: dict) -> bool:
    """
    Using two result.csv files received model management metrics,
    find which of them is improves performance.
    :param previous_model_metrics: dataframe of previous best model performance
    :param current_model_metrics: dataframe of current model performance
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

    def _pad_to_match(_previous: pd.DataFrame, _current: pd.DataFrame) -> (pd.DataFrame, pd.DataFrame):
        """
        Pad the shorter metric to match the longer one.
        :param _previous: previous model metrics
        :param _current: current model metrics
        :return: padded previous and current metrics
        """
        len_diff = abs(len(_previous) - len(_current))
        if len(_previous) > len(_current):
            _current = pd.concat([_current, pd.Series([_current.iloc[-1]] * len_diff)])
        else:
            _previous = pd.concat([_previous, pd.Series([_previous.iloc[-1]] * len_diff)])
        return _previous, _current

    def _compare(_previous: pd.DataFrame, _current: pd.DataFrame, **kwargs):
        if len(_previous) != len(_current):
            logging.warning("Compare non matching sizes, shorter metric will be padded to match.")
            _previous, _current = _pad_to_match(_previous, _current)
        assert len(_previous) == len(_current), "Cannot compare non matching sizes," \
                                                " please check testing results file validity."

        delta = kwargs.get("min_delta", 0)
        check = np.any if kwargs.get("soft_check", False) else np.all
        sign = np.negative if kwargs.get("lower_is_better_metrics", False) else np.array
        _diff = _current.values - _previous.values

        # precision:    previous        current
        #               0.5             0.6         ->  0.1
        #               0.4             0.4         ->  0.0
        #               0.3             0.2         -> -0.1

        _comparison_result = check(sign(_diff) >= delta)

        return _comparison_result

    def _verbose(_previous: np.ndarray, _current: np.ndarray, **kwargs):
        print(f'[{idx}] performing comparison on {single_metric_name} metric between:')
        comparison = pd.DataFrame({
            "previous model": _previous,
            "current model": _current
        })
        comparison.columns.name = "TH"
        comparison = comparison.set_axis(axes)
        print(comparison, end='\n\n')

    def _filter(_previous_metric: pd.DataFrame, _current_metric: pd.DataFrame, **kwargs):
        """
        concatenate filtering over the dataFrames before performing metrics comparison
        :param _previous_metric: previous metric table
        :param _current_metric: current metric table
        :param kwargs: filter options
        :return: filtered tables
        """

        def _range_query(table, col, rng):
            return table.loc[table[col].isin(rng)]

        threshold = kwargs.get("iou_threshold", None)
        labels = kwargs.get("specific_label", None)
        metric_name = kwargs.get("metric_name", None)

        if kwargs.get("same_pre_model", False):
            assert set(_previous_metric["premodel"]) == set(_current_metric["premodel"]), \
                "non-matching pre-models detected"

        if threshold:
            # for [0.1, 0.5], numpy will return [0.1 ,..., 0.4]
            _rv = np.arange(*threshold, 0.1) if type(threshold) is list else np.arange(threshold, 1, 0.1)
            _rv = np.round(_rv.astype(np.float64), 1)
            # extract rows matching the range value
            _previous_metric = _range_query(
                _previous_metric, _previous_metric.columns[0], _rv
            )  # _p.loc['_p[_p.columns[0]].isin(_rv)]
            _current_metric = _range_query(_current_metric, _current_metric.columns[0], _rv)

        if labels:  # TODO rename to be able to filter by dataset labels
            _previous_metric = _range_query(_previous_metric, "label", labels)  # _p.loc[_p["label"].isin(labels)]
            _current_metric = _range_query(_current_metric, "label", labels)

        if metric_name:
            _previous_metric = _previous_metric[_previous_metric["label"] == metric_name]
            _current_metric = _current_metric[_current_metric["label"] == metric_name]

        # store X axes (to display -- F(threshold)=result -- function)
        _axes = _previous_metric[_previous_metric.columns[0]].values

        return _previous_metric, _current_metric, _axes

    conclusions = []
    previous_sheet = previous_model_metrics
    current_sheet = current_model_metrics
    opt_handlers: dict = {
        "verbose": _verbose,
    }

    for idx, single_metric in enumerate(configuration.items(), start=1):
        if type(single_metric[1]) is dict:
            single_metric_name, config = single_metric
            previous_metric, current_metric, axes = _filter(previous_sheet,
                                                            current_sheet,
                                                            **{"metric_name": single_metric_name, **config})

            for key in config.keys():
                if config.get(key, False):
                    opt_handlers.get(key, lambda a, b: None)(previous_metric.values, current_metric.values)

            result = _compare(previous_metric, current_metric, **config)
            conclusions.append(result)

    return np.array(conclusions).all()
