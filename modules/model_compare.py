import os
import json
import logging
import dtlpy as dl
import numpy as np
import pandas as pd

from dtlpymetrics.scoring import calc_precision_recall
from sklearn.metrics import auc

logger = logging.getLogger('ModelCompare')
logger.setLevel(logging.INFO)


class ModelComparer(dl.BaseServiceRunner):
    """
    A class for comparing two models according to user-specified metrics.
    """

    @staticmethod
    def metrics_to_df(model: dl.Model) -> pd.DataFrame:
        """
        Converts the metrics of a model to a pandas DataFrame with x and y columns.

        Args:
            model (dl.Model): Model entity from which to download metrics

        Returns:
            pd.DataFrame: DataFrame containing the model's metric scores with x and y columns
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

    @staticmethod
    def get_eval_df(previous_model: dl.Model, new_model: dl.Model, dataset: dl.Dataset, compare_config: dict):
        """
        Get evaluation dataframe for each model based on the metrics specified in the compare_config.

        Args:
            previous_model (dl.Model): The original/previous model to compare against
            new_model (dl.Model): The new model to be evaluated
            dataset (dl.Dataset): Dataset containing the test subset for model evaluation
            compare_config (dict): Configuration specifying which metrics to compare
                                  If empty, defaults to comparing annotation scores

        Note:
            Currently supports precision-recall metrics. Other metrics will trigger
            a NotImplementedError warning.
        """

        for metric_name, metric_config in compare_config.items():
            if metric_name == 'precision_recall':
                iou_threshold = metric_config.get('iou_threshold', 0.5)
                current_pr_df = calc_precision_recall(
                    dataset_id=dataset.id,
                    model_id=previous_model.id,
                    iou_threshold=iou_threshold,
                    method_type='every_point',
                )

                new_pr_df = calc_precision_recall(
                    dataset_id=dataset.id, model_id=new_model.id, iou_threshold=iou_threshold, method_type='every_point'
                )
                metric_config['current_model_metrics'] = current_pr_df
                metric_config['new_model_metrics'] = new_pr_df
            else:
                logger.warning(
                    NotImplementedError(f"Metric {metric_name} is not implemented, use precision_recall instead.")
                )
                continue

    @staticmethod
    def compare_model_training(
        current_model_metrics: pd.DataFrame, new_model_metrics: pd.DataFrame, configuration: dict
    ) -> bool:
        """
        Compare training metrics between two models.

        Args:
            current_model_metrics (pd.DataFrame): Metrics from the current/previous model
            new_model_metrics (pd.DataFrame): Metrics from the new model
            configuration (dict): Configuration specifying comparison criteria including:
                - wins: Strategy for determining if new model is better ('any', 'all', or float ratio)
                - checks: List of checks to perform
                - verbose: Whether to log detailed comparison information

        Returns:
            bool: True if the new model is better according to the configuration criteria

        Note:
            Each check in the configuration can specify:
            - min_delta: Minimum required difference for improvement
            - maximize: Whether higher values are better
            - figure: Which metric figure to compare
            - legend: Which legend entry to compare
            - x_index: Which x value to compare at
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
            current_values = current_model_metrics.loc[
                (current_model_metrics['figure'] == figure) & (current_model_metrics['legend'] == legend)
            ]
            current_x = current_values['x'].values
            current_y = current_values['y'].values

            if len(current_x) == 0 or len(current_y) == 0:
                raise ValueError(f"Could not find figure {figure} and legend {legend} in current model metrics")
            # TODO check the number of returned values and warn if there is more than one
            current_value = current_y[current_x == current_x[x_index]][0]
            # now we filter the new model Dataframe by column values
            new_values = new_model_metrics.loc[
                (new_model_metrics['figure'] == figure) & (new_model_metrics['legend'] == legend)
            ]
            new_x = new_values['x'].values
            new_y = new_values['y'].values
            if len(new_x) == 0 or len(new_y) == 0:
                raise ValueError(f"Could not find figure {figure} and legend {legend} in current model metrics")
            # TODO check the number of returned values and warn if there is more than one
            new_value = new_y[new_x == new_x[x_index]][0]
            if maximize is True:
                win_check = new_value > (current_value + min_delta)
            else:
                win_check = new_value < (current_value - min_delta)
            new_model_wins.append(win_check)

            if verbose is True:
                logger.info(
                    f'Compare: figure: {figure}, legend: {legend}. Configs: maximize: {maximize}, min_delta: {min_delta}, current_value: {current_value}, new_value: {new_value}. New model won? {win_check}'
                )

        # TODO check all config return types
        logger.info(f"Finished model comparison, wins list: {new_model_wins}")

        return ModelComparer.check_check_if_winning(wins, new_model_wins)

    @staticmethod
    def compare_models(
        previous_model: dl.Model,
        new_model: dl.Model,
        progress: dl.Progress,
        context: dl.Context,
        compare_config: dict = None,
        dataset: dl.Dataset = None,
    ) -> dl.Model:
        """
        Compare metrics of two models to determine which is better.

        Args:
            previous_model (dl.Model): The original/previous model
            new_model (dl.Model): The new model to compare against
            progress (dl.Progress): Progress tracker for updating action status
            context (dl.Context): Context of the function execution
            compare_config (dict, optional): Configuration for comparison metrics
            dataset (dl.Dataset, optional): Dataset for evaluation-based comparison

        Returns:
            dl.Model: The winning model (either new_model or previous_model)

        Note:
            If no compare_config is provided, uses default configuration from
            pipeline_configs/compare_configurations.json. Updates model metadata
            with comparison results if configured to do so.
        """
        logger.info(f"Compare configuration: {compare_config}")

        # loading default compare_config
        default_compare_config_path = os.path.join('pipeline_configs', 'compare_configurations.json')
        with open(default_compare_config_path, 'r') as f:
            default_compare_config = json.load(f)

        if compare_config is None:
            logger.warning("No metrics were specified in the compare_config. Using precision-recall by default.")
            compare_config = default_compare_config

        if 'precision_recall' not in compare_config:
            logger.warning("Precision recall not specified in compare_config. Using default values.")
            compare_config['precision_recall'] = default_compare_config.get('precision_recall', dict())

        if dataset is None:
            # compare by model training
            is_improved = ModelComparer.compare_model_training(
                current_model_metrics=ModelComparer.metrics_to_df(previous_model),
                new_model_metrics=ModelComparer.metrics_to_df(new_model),
                configuration=compare_config,
            )
        else:
            ModelComparer.get_eval_df(
                previous_model=previous_model, new_model=new_model, compare_config=compare_config, dataset=dataset
            )
            is_improved = ModelComparer.compare_model_evaluation(configuration=compare_config)
        winning_model = new_model if is_improved else previous_model

        actions = ['update model', 'discard']
        logger.info(f"Is new model better? {is_improved}")
        if is_improved is True:
            logger.info(f"Action {actions[0]}")
            progress.update(action=actions[0])
        else:
            logger.info(f"Action to update {actions[1]}")
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

    @staticmethod
    def check_check_if_winning(wins, new_model_wins):
        """
        Determine if the new model is winning based on the specified winning criteria.

        Args:
            wins (str or float): Winning criteria:
                - 'all': New model must win all comparisons
                - 'any': New model must win at least one comparison
                - float: New model must win this ratio of comparisons
            new_model_wins (list): List of boolean results from individual comparisons

        Returns:
            bool: True if the new model meets the winning criteria
        """
        if wins == 'all':
            is_winning = True if all(new_model_wins) else False
        elif wins == 'any':
            is_winning = True if any(new_model_wins) else False
        elif isinstance(wins, float):
            is_winning = True if (sum(new_model_wins) / len(new_model_wins)) > wins else False
        else:
            is_winning = False
        return is_winning

    @staticmethod
    def _compare_annotation_scores(_current: pd.DataFrame, _new: pd.DataFrame, **kwargs):
        """
        Compare annotation scores between two models.

        Args:
            _current (pd.DataFrame): Current model's annotation scores
            _new (pd.DataFrame): New model's annotation scores
            **kwargs: Additional parameters including:
                - annotation_scores (dict): Configuration for score comparison
                - win_ratio (float): Required ratio of wins for new model to be considered better

        Note:
            Updates kwargs with 'new_model_won' boolean indicating comparison result.
            Raises ValueError if win_ratio is not a float.
        """
        wins = kwargs.get('annotation_scores', dict()).get('win_ratio', 0)
        if isinstance(wins, float) is False:
            raise ValueError(f"wins should be a float, got {wins} of type {type(wins)}")

        item_scores_old = _current.groupby(['item_id'])['annotation_score'].mean()
        item_scores_new = _new.groupby(['item_id'])['annotation_score'].mean()
        new_model_wins = np.array(item_scores_new > item_scores_old)

        if wins == 1:
            is_winning = True if all(new_model_wins) else False
        elif wins == 0:
            is_winning = True if any(new_model_wins) else False
        else:
            sum_model_wins = sum(new_model_wins)
            all_model_wins = len(new_model_wins) if not len(new_model_wins) == 0 else 1
            is_winning = True if (sum_model_wins / all_model_wins) > wins else False
        kwargs['new_model_won'] = is_winning

    @staticmethod
    def compare_model_evaluation(configuration: dict) -> bool:
        """
        Compare two models based on their predictions on a dataset.

        Args:
            configuration (dict): Configuration specifying comparison metrics and criteria

        Returns:
            bool: True if the new model performs better according to the configuration

        Note:
            Currently supports comparison based on precision-recall curves and annotation scores.
        """
        # summarize scores by *item*
        # annotation scores are an average of all three: label, attribute, iou
        is_improved = ModelComparer._compare(configuration=configuration)

        logger.warning(f"finished comparing, new model won : {is_improved}")

        return is_improved

    @staticmethod
    def _compare(configuration: dict) -> bool:
        """
        Compare model performance metrics between two result.csv files to determine
        which model performs better according to specified criteria.
        :param configuration: Dictionary containing comparison settings and thresholds
                            for different metrics (see Keyword Arguments below)
        :Keyword Arguments:

        ******* SPECIFIC METRIC *******
        * *precision-recall* (``dict``) --
          compare models by Precision-Recall metrics using AUC-PR

        ******* SETTINGS *******
        * *iou_threshold* (``float``) --
          perform comparison based on specific (single/boundaries) IoU value [default: 0.5]
        * *specific_label* (``list``) --
          perform comparison based on specific label [default: everything]
        * *min_delta* (``float``) --
          require minimum difference between the metrics before considering it as improvement [default: 0]

        :return: True if the comparison detected any improvement OR equalization, else - False.
        """

        def _compare_auc_pr(_current: pd.DataFrame, _new: pd.DataFrame, **kwargs):
            """
            Compare two models by Precision-Recall metrics using AUC-PR.
            :param _current: current model metrics dataframe
            :param _new: new model metrics dataframe
            :return:
            """
            new_model_won = False
            min_delta = kwargs.get("min_delta", 0)

            # Sort the precision and recall values together.
            current_precision_np = np.asarray(_current['precision'])
            current_recall_np = np.asarray(_current['recall'])
            current_sorted_precision_recall = np.array([current_precision_np, current_recall_np]).T
            sorted_indices = current_sorted_precision_recall[:, 1].argsort()[::-1]
            current_sorted_precision_recall = current_sorted_precision_recall[sorted_indices]

            # Calculate the AUC-PR.
            current_auc_pr = auc(current_sorted_precision_recall[:, 1], current_sorted_precision_recall[:, 0])
            logger.info(f"current model auc pr: {current_auc_pr}")
            print(f"current model auc pr: {current_auc_pr}")

            # Sort the precision and recall values together.
            new_precision_np = np.asarray(_new['precision'])
            new_recall_np = np.asarray(_new['recall'])
            new_sorted_precision_recall = np.array([new_precision_np, new_recall_np]).T
            sorted_indices = new_sorted_precision_recall[:, 1].argsort()[::-1]
            new_sorted_precision_recall = new_sorted_precision_recall[sorted_indices]

            # Calculate the AUC-PR.
            new_auc_pr = auc(new_sorted_precision_recall[:, 1], new_sorted_precision_recall[:, 0])
            logger.info(f"new model auc pr: {new_auc_pr}")
            print(f"new model auc pr: {new_auc_pr}")

            difference_auc_pr = new_auc_pr - current_auc_pr
            if difference_auc_pr > min_delta:
                new_model_won = True

            kwargs['new_model_won'] = new_model_won
            return new_model_won

        def _filter(_current_metric: pd.DataFrame, _new_metric: pd.DataFrame, **kwargs):
            """
            concatenate filtering over the dataFrames before performing metrics comparison
            :param _current_metric: current metric table
            :param _new_metric: new metric table
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
                _current_metric = _range_query(_current_metric, "label", labels)
                _new_metric = _range_query(_new_metric, "label", labels)

            return _current_metric, _new_metric

        compare_funcs = {
            'precision_recall': _compare_auc_pr,
            'annotation_scores': ModelComparer._compare_annotation_scores,
        }
        result = False
        for metric_name, metric_config in configuration.items():
            if not metric_name == 'precision_recall':
                continue
            compare_func = compare_funcs.get(metric_name, None)
            current_sheet = metric_config.get('current_model_metrics')
            new_sheet = metric_config.get('new_model_metrics')
            current_metric, new_metric = _filter(current_sheet, new_sheet, **metric_config)

            result = compare_func(current_metric, new_metric, **metric_config)
        return result
