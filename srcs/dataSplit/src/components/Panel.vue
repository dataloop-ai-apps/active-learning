<script setup lang="ts">
import { v4 } from 'uuid'
import { cloneDeep, debounce, sumBy } from 'lodash'
import { watch, ref, defineProps, computed, toRef, onUpdated  } from 'vue-demi'
import {
    Group,
    NodeConfig,
    ValidationDescriptor,
    NodeDescriptor
} from '../models/PipelineNode'
import { toFloat } from '../models/utils'
import { DlFrameEvent } from '@dataloop-ai/jssdk'

const props = defineProps<{ component: NodeDescriptor; readonly: boolean; addItemMetadata: boolean}>()
const emit = defineEmits(['addItemMetadata'])

const component = toRef(props, 'component')
const readonly = toRef(props, 'readonly')
const MAX_GROUP_NUMBER = 5
const MIN_GROUP_NUMBER = 2
const MAX_DISTRIBUTION = 100
const nodeName = ref(NodeConfig.DefaultValues.name)
const distributeEqually = ref(NodeConfig.DefaultValues.distributeEqually)
const metadataKeySpecialCharError = ref(false)
const groups = ref<Group[]>(NodeConfig.DefaultValues.groups)
const addItemMetadata = computed({
    get: () => {
        return props.addItemMetadata
    },
    set: (val) => {
        emit('addItemMetadata', val)
    }
})

/** Whether adding groups is allowed */
const canAddGroup = computed(() => {
    return groups.value.length < MAX_GROUP_NUMBER
})

/** Whether deleting groups is allowed */
const canDelete = computed(() => {
    return groups.value.length > MIN_GROUP_NUMBER
})

onUpdated(() => {
    window.dl.agent.sendEvent({
        name: "app:setHeight",
        payload: document.body.scrollHeight
    })
})

const changeDistribution = () => {
    if (!distributeEqually.value) {
        return
    }
    for (const group of groups.value) {
        group.distribution = toFloat(100 / groups.value.length)
    }

    if (remaining.value > 0) {
        groups.value[groups.value.length - 1].distribution = toFloat(
            groups.value[groups.value.length - 1].distribution + remaining.value
        )
    }
}

/** Creates a new group if allowed */
const onClick = () => {
    if (groups.value.length >= MAX_GROUP_NUMBER) {
        return
    }
    groups.value.push({
        id: v4(),
        name: ``,
        distribution: toFloat(remaining.value > 0 ? remaining.value : 0)
    })
    changeDistribution()
}

/** Group deletion by id if allowed */
const onDelete = (id: string) => {
    if (canDelete.value) {
        groups.value = groups.value.filter((g) => g.id !== id)
        changeDistribution()
    }
}

/** Sum of all group distributions */
const groupsSum = computed(() => {
    const groupsNumbered = groups.value.map((g) => ({
        ...g,
        distribution: Number(g.distribution)
    }))
    return toFloat(sumBy(groupsNumbered, 'distribution'))
})

/** Whether the sum of all group distributions is greater than MAX_DISTRIBUTION */
const isDistributionError = computed(() => {
    return groupsSum.value > MAX_DISTRIBUTION
})

/** Whether the sum of all group distributions is less than MAX_DISTRIBUTION */
const isDistributionWarning = computed(() => {
    return groupsSum.value < MAX_DISTRIBUTION
})

/** The remaining distribution to be distributed */
const remaining = computed(() => {
    return toFloat(MAX_DISTRIBUTION - groupsSum.value)
})

const remainingAbs = computed(() => {
    return Math.abs(remaining.value)
})


/** Validation of the distribution of a group */
const validateDistribution = debounce((index: number) => {
    const updated = cloneDeep(groups.value)
    updated[index].distribution = toFloat(
        Math.max(
            Math.min(Number(updated[index].distribution), MAX_DISTRIBUTION),
            0
        )
    )
    Object.assign(groups.value, updated)
}, 0)

/** Validation of the group name */
const validateGroupName = (val: string, index: number) => {
    try {
        if (typeof val !== 'string') {
            return
        }
        const updated = cloneDeep(groups.value)
        updated[index].name = val?.replace(/[^\w_]/g, '') || ''
        Object.assign(groups.value, updated)
    } catch (error) {
        console.log(`Failed to validate group name`, { error })
    }
}

/** Validation of the metadata key */
const validateMetadataKey = (val: string) => {
    if (typeof val !== 'string') {
        return
    }
    metadataKeySpecialCharError.value = new RegExp(/[^\w_\-\.]/g).test(val)
}

/** Whether the distribution is valid */
const isDistributionValid = computed(() => {
    return !isDistributionWarning.value && !isDistributionError.value
})

/** Whether all groups are valid */
const areGroupsValid = computed(() => {
    return groups.value.every((g) => !!g.name.length)
})

const nodeNameErrorMessage = computed(() => {
    if (!nodeName.value.length) {
        return 'Node name is required'
    }
    if (!nodeName.value.match(/^[a-zA-Z0-9_\- ]+$/)) {
        return 'Node name can only contain letters, numbers, underscores, hyphens and spaces'
    }
})

const trimNodeName = () => {
    nodeName.value = nodeName.value.trim()
}

const errors = computed((): { message: string; suggestion: string }[] => {
    const e = []
    if (isDistributionError.value || isDistributionWarning.value) {
        e.push({
            message: 'Distribution must equal 100%',
            suggestion: 'Please adjust the distribution'
        })
    }
    if (!!nodeNameErrorMessage.value) {
        e.push({
            message: 'Node name error',
            suggestion: 'Please adjust the node name'
        })
    }
    if (!areGroupsValid.value) {
        e.push({
            message: 'Group name is required',
            suggestion: 'Please adjust the group name'
        })
    }
    return e
})

const validation = computed((): ValidationDescriptor => {
    return {
        valid: errors.value.length === 0,
        errors: errors.value
    }
})

/** Sends the updated node config to the platform */
const debouncedUpdate = debounce(async () => {
    const nodeConfig = new NodeConfig({
        name: nodeName.value.trim(),
        groups: groups.value,
        distributeEqually: distributeEqually.value,
        validation: validation.value,
        itemMetadata: addItemMetadata.value
    })
    try {
        component.value.metadata.customNodeConfig = nodeConfig
        component.value.outputs = 
            [{
                portId: component.value.outputs[0].portId ?? v4(),
                actions: nodeConfig.groups.filter((dict) => dict.name.trim() !== '').map(element => { return element.name }) ?? [],
                name: 'item',
                nodeId: component.value.id,
                type: 'Item'
            }]
        await window.dl.agent.sendEvent({
            name: DlFrameEvent.UPDATE_NODE_CONFIG,
            payload: component.value
        })
    } catch (error) {
        console.error(`Failed to send event`, { error })
    }
}, 200)

watch(
    [nodeName, groups, distributeEqually, validation, addItemMetadata],
    debouncedUpdate,
    {
        deep: true
    }
)

watch(component, () => {
    const nodeConfig = component.value?.metadata.customNodeConfig
    nodeName.value = nodeConfig.name
    groups.value = nodeConfig.groups
    distributeEqually.value = nodeConfig.distributeEqually
})
</script>

<template>
    <div id="panel">
        <dl-input
            dense
            style="width: 100%; padding-bottom: 20px"
            placeholder="Insert node name"
            :error="!!nodeNameErrorMessage"
            :error-message="nodeNameErrorMessage"
            v-model="nodeName"
            title="Node Name"
            required
            @blur="trimNodeName"
            :disabled="readonly"
        />
        <div>
            <dl-typography size="12px" color="dl-color-darker"
                >Subsets Distribution</dl-typography
            >
            <dl-typography color="dl-color-medium" style="margin-top: 6px" size="10px">
                Refine the model data distribution into training, validation, and test subsets
            </dl-typography>
            <dl-checkbox
                style="margin-top: 18px"
                v-model="distributeEqually"
                label="Distribute equally"
                :disabled="readonly"
            />
            <dl-list padding="0">
                <dl-list-item padding="0" class="container">
                    <dl-item-section color="dl-color-medium" class="item"
                        >Subset Name</dl-item-section
                    >
                    <dl-item-section color="dl-color-medium" class="item-2"
                        >Distribution</dl-item-section
                    >
                </dl-list-item>
                <dl-list-item
                    padding="0"
                    v-for="(group, index) in groups"
                    :key="group.id"
                    height="fit-content"
                    class="container"
                    id="groups-distribution"
                    style="margin-bottom: 10px; align-items: start"
                >
                    <dl-item-section class="item">
                        <dl-input
                            disable-clear-btn
                            v-model="group.name"
                            placeholder="Insert group name"
                            :error="group.name.length === 0"
                            error-message="Group name is required"
                            dense
                            :disabled="readonly"
                            v-bind="{disabled:true}"
                            @input="validateGroupName($event, index)"
                            @change="validateGroupName($event, index)"
                        />
                    </dl-item-section>
                    <dl-item-section
                        class="item-2"
                        style="display: flex; align-items: center; gap: 10px"
                    >
                        <dl-input
                            style="width: 100%"
                            disable-clear-btn
                            type="number"
                            :error="isDistributionError"
                            :warning="isDistributionWarning"
                            :disabled="distributeEqually"
                            v-model.number="group.distribution"
                            @blur="validateDistribution(index)"
                            dense
                        >
                            <template #append> % </template>
                        </dl-input>
                    </dl-item-section>
                </dl-list-item>
                <dl-list-item padding="0">
                    <dl-item-section
                        style="
                            gap: 5px;
                            text-align: right;
                        "
                    >
                        <div style="width: 100% font-size: 10px">
                            <dl-typography color="dl-color-darker">
                                {{ groupsSum }}%
                            </dl-typography>
                            <dl-typography
                                v-if="isDistributionWarning"
                                color="dl-color-warning"
                            >
                                <dl-icon icon="icon-dl-alert-filled" />
                                {{ remaining }}% Remaining
                            </dl-typography>
                            <dl-typography
                                v-else-if="isDistributionError"
                                color="dl-color-negative"
                            >
                                <dl-icon icon="icon-dl-error-filled" />
                                {{ remainingAbs }}
                                Exceeding
                            </dl-typography>
                            <dl-typography v-else color="dl-color-lighter">
                                Total distribution
                            </dl-typography>
                        </div>
                        <div style="width: 20px"></div>
                    </dl-item-section>
                </dl-list-item>
            </dl-list>
        </div>
        <dl-list-item bordered style="margin-top: 20px" height="20px" />
        <div id="item-metadata-section">
            <dl-typography size="12px" color="dl-color-darker">
                Item Tags
                <dl-icon icon="icon-dl-info" size="13px" />
                <dl-tooltip>
                    Add a tag to each item according to its assigned subset group. The tag will be added to a dictionary under item.metadata.system.tags in the following format: tags = {“subset name”: true} 
                </dl-tooltip>
            </dl-typography>
            <dl-checkbox
                style="margin-top: 10px"
                v-model="addItemMetadata"
                label="Tag items based on their assigned subset name"
                :disabled="readonly"
                v-bind="{disabled:true}"
            />
        </div>
    </div>
</template>

<style>
#groups-distribution > .dl-list-item {
    align-items: start !important;
}

.container {
    display: flex;
    flex-direction: row;
}

.dl-item__section--main {
    flex: 1 1 100% !important;
}

.dl-list-item {
    gap: 5px;
}

.item {
    flex-shrink: 1 !important;
    width: 100% !important;
}
.item-2 {
    flex-shrink: 1.3 !important;
    width: 100% !important;
}
</style>
