<script setup lang="ts">
// This starter template is using Vue 3 <script setup> SFCs
// Check out https://vuejs.org/api/sfc-script-setup.html#script-setup
import Panel from './components/Panel.vue'
import { DlEvent, DlFrameEvent } from '@dataloop-ai/jssdk'
import { onMounted, ref } from 'vue'
import { NodeConfig, NodeDescriptor } from './models/PipelineNode'

const component = ref<NodeDescriptor>(null)
const theme = ref('light')
const readonly = ref('edit')

onMounted(() => {
    try {
        window.dl.init()
        const dl = window.dl
        dl.on(DlEvent.READY, async () => {
            try {
                const settings = await dl.settings.get() as any
                theme.value = settings.theme
                readonly.value = settings.readonly
            } catch (e) {
                throw new Error('Error getting settings', e)
            }

            dl.on(DlEvent.THEME, (mode: string) => {
                theme.value = mode
            })

            dl.on('setReadonly', (readonlyValue: string) => {
                readonly.value = readonlyValue
            })

            dl.on(DlEvent.NODE_CONFIG, async (eventPayload: NodeDescriptor) => {
                try {
                    if (!eventPayload.metadata.customNodeConfig){
                        eventPayload.metadata.customNodeConfig = NodeConfig.DefaultValues
                    }
                    component.value = new NodeDescriptor(NodeDescriptor.fromJSON(eventPayload))
                    console.info('Node Config Event', eventPayload)
                    await window.dl.agent.sendEvent({
                        name: DlFrameEvent.UPDATE_NODE_CONFIG,
                        payload: component.value
                    })
                } catch (e) {
                    throw new Error(
                        'Error creating NodeConfig from nodeConfig event',
                        e
                    )
                }
            })
        })
    } catch (e) {
        console.error('Error initializing xFrameDriver', e)
    }
})
</script>

<template>
    <dl-theme-provider :is-dark="theme === 'dark'">
        <div class="full-screen">
            <Panel :theme="theme" :component="component" :readonly="readonly === 'view'"/>
        </div>
    </dl-theme-provider>
</template>

<style scoped></style>
