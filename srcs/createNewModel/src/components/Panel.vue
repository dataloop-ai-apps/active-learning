<script setup lang="ts">
import { ref, defineProps, computed, toRef, nextTick, onUpdated } from 'vue'
import { cloneDeep, debounce, sumBy } from 'lodash'
import { watch } from 'vue-demi'
import {
    NodeConfig,
    ValidationDescriptor,
    NodeDescriptor
} from '../models/PipelineNode'
import { toFloat } from '../models/utils'
import { DlFrameEvent } from '@dataloop-ai/jssdk'

const props = defineProps<{ component: NodeDescriptor; readonly: boolean }>()
const readonly = toRef(props, 'readonly')
const component = toRef(props, 'component')
const nodeName = ref(NodeConfig.DefaultValues.name)
const modelName = ref(NodeConfig.DefaultValues.modelName)

onUpdated(() => {
    window.dl.agent.sendEvent({
        name: DlFrameEvent.SET_HEIGHT,
        payload: document.body.scrollHeight
    })
})

const nodeNameErrorMessage = computed(() => {
    if (!nodeName.value.length) {
        return 'Node name is required'
    }
    if (!nodeName.value.match(/^[a-zA-Z0-9_\- ]+$/)) {
        return 'Node name can only contain letters, numbers, underscores, hyphens and spaces'
    }
})

const newModelNameErrorMessage = computed(() => {
    if (!modelName.value.length) {
        return 'New model name is required'
    }
})

const trimNodeName = () => {
    nodeName.value = nodeName.value.trim()
}

const errors = computed((): { message: string; suggestion: string }[] => {
    const e = []

    if (!!nodeNameErrorMessage.value) {
        e.push({
            message: 'Node name error',
            suggestion: 'Please adjust the node name'
        })
    }
    if (newModelNameErrorMessage.value) {
        e.push({
            message: 'new model name error',
            suggestion: 'Please adjust the new model name'
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
        modelName: modelName.value.trim(),
        modelParameters: {},
        validation: validation.value,
    })
    try {
        component.value.metadata.customNodeConfig = nodeConfig
        await window.dl.agent.sendEvent({
            name: DlFrameEvent.UPDATE_NODE_CONFIG,
            payload: component.value
        })
    } catch (error) {
        console.error(`Failed to send event`, { error })
    }
}, 200)

watch(
    [nodeName, validation, modelName],
    debouncedUpdate,
    {
        deep: true
    }
)

watch(component, () => {
    const nodeConfig = component.value?.metadata.customNodeConfig
    nodeName.value = nodeConfig.name
    modelName.value = nodeConfig.modelName
})
</script>

<template>
    <div id="panel">
        <dl-text-input
            without-root-padding
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
        <dl-text-input
            without-root-padding
            style="width: 100%; padding-bottom: 20px"
            placeholder="Insert a model name"
            :error="!!newModelNameErrorMessage"
            :error-message="newModelNameErrorMessage"
            v-model="modelName"
            title="New Model Name"
            tooltip="The model name should be formatted as a Python string. To prevent duplication of model names, include dynamic variables within curly braces."
            required
            @blur="trimNodeName"
            :disabled="readonly"
        />
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
