<script setup lang="ts">
import { ref, defineProps, computed, toRef, onUpdated } from 'vue'
import {debounce } from 'lodash'
import { watch } from 'vue-demi'
import {
    NodeConfig,
    ValidationDescriptor,
    NodeDescriptor
} from '../models/PipelineNode'
import { DlFrameEvent } from '@dataloop-ai/jssdk'

const props = defineProps<{ component: NodeDescriptor; readonly: boolean }>()
const readonly = toRef(props, 'readonly')
const component = toRef(props, 'component')

const nodeName = ref(NodeConfig.DefaultValues.name)

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
    if (!!nodeNameErrorMessage.value) {
        e.push({
            message: 'Node name error',
            suggestion: 'Please adjust the node name'
        })
    }
    return e
})
onUpdated(() => {
    window.dl.agent.sendEvent({
        name: DlFrameEvent.SET_HEIGHT,
        payload: document.body.scrollHeight
    })
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
    [nodeName, validation],
    debouncedUpdate,
    {
        deep: true
    }
)

watch(component, () => {
    const nodeConfig = component.value?.metadata.customNodeConfig
    nodeName.value = nodeConfig.name
})
</script>

<template>
    <div id="panel">

        <dl-typography color="dl-color-lighter">
            The predict() function of the selected application will be invoked during the prediction process.
        </dl-typography>

        <dl-input
            without-root-padding
            style="width: 100%; padding: 20px 0"
            placeholder="Insert node name"
            :error="!!nodeNameErrorMessage"
            :error-message="nodeNameErrorMessage"
            v-model="nodeName"
            title="Node Name"
            required
            @blur="trimNodeName"
            :disabled="readonly"
        />

    </div>
</template>

