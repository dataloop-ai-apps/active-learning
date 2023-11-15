<script setup lang="ts">
import { ref, defineProps, computed, toRef, onMounted, onUpdated} from 'vue'
import {debounce } from 'lodash'
import { watch } from 'vue-demi'
import {
    NodeConfig,
    ValidationDescriptor,
    NodeDescriptor,
    CODEBASE_TYPES,
    CODEBASE_TYPES_OPTIONS
} from '../models/PipelineNode'
import { DlFrameEvent } from '@dataloop-ai/jssdk'
import ace from 'ace-builds'
// import 'ace-builds/webpack-resolver'
import beautify from 'ace-builds/src-noconflict/ext-beautify'

const props = defineProps<{ component: NodeDescriptor; readonly: boolean; theme: string }>()
const readonly = toRef(props, 'readonly')
const component = toRef(props, 'component')
const theme = toRef(props, 'theme')

const nodeName = ref(NodeConfig.DefaultValues.name)
const isCodebase = ref(NodeConfig.DefaultValues.isCodebase)
const nodeCodebaseType = ref(NodeConfig.DefaultValues.codebaseType)
const nodeCode = ref(NodeConfig.DefaultValues.code)
const nodeZipInput = ref(NodeConfig.DefaultValues.zipInput)
const nodeGitUrl = ref(NodeConfig.DefaultValues.gitUrl)
const nodeGitTag = ref(NodeConfig.DefaultValues.gitTag)

const nodeFileInput = ref(null);
const nodeRequirementsFileInput = ref(null);
const editor = ref(null);

const codebaseType = ref(CODEBASE_TYPES_OPTIONS[0])
const openEditPanel = ref(false)


onUpdated(() => {
    window.dl.agent.sendEvent({
        name: DlFrameEvent.SET_HEIGHT,
        payload: document.body.scrollHeight
    })
})

onMounted(() => {
    nodeFileInput.value = document.createElement('input');
    nodeFileInput.value.type = 'file';
    nodeFileInput.value.style.display = 'none';
    nodeFileInput.accept = '.zip';
    nodeFileInput.value.addEventListener('change', handleFileUpload);
    document.body.appendChild(nodeFileInput.value);

    nodeRequirementsFileInput.value = document.createElement('input');
    nodeRequirementsFileInput.value.type = 'file';
    nodeRequirementsFileInput.value.style.display = 'none';
    nodeRequirementsFileInput.accept = '.txt';
    nodeRequirementsFileInput.value.addEventListener('change', handleRequirementsUpload);
    document.body.appendChild(nodeRequirementsFileInput.value);

    // editor.value = ace.edit('editor', {mode: ace.require('ace/mode/python')});
    // editor.value.session.setMode('python')
    // editor.value.on('change', handleCodeChange)
    // setEditorTheme()
});

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

const validation = computed((): ValidationDescriptor => {
    return {
        valid: errors.value.length === 0,
        errors: errors.value
    }
})

const setEditorTheme = () => {
    if (theme.value === 'light') {
        editor.value.setTheme(ace.require('ace/theme/tomorrow'))
    } else {
        editor.value.setTheme(ace.require('ace/theme/tomorrow_night'))
    }
}

const openFileUpload = () : void => {
    nodeFileInput.value.click();
}

const handleFileUpload = (event: Event): void => {
    const file = (event.target as HTMLInputElement)?.files[0];
    if (!file) {
        return;
    }

    // Check if file type is .zip
    const allowedFileType = 'application/zip';
    if (file.type !== allowedFileType) {
        // TODO: handle type check here.
        return;
    }

    // Do something with the uploaded file here
    nodeFileInput.value = file
}

const openRequirementsFileUpload = () : void => {
    nodeRequirementsFileInput.value.click();
}

const handleRequirementsUpload = (event: Event): void => {
    const file = (event.target as HTMLInputElement)?.files[0];
    if (!file) {
        return;
    }

    // Check if file type is .zip
    const allowedFileType = 'text/plain';
    if (file.type !== allowedFileType) {
        // TODO: handle type check here.
        return;
    }

    // Do something with the uploaded file here
    nodeRequirementsFileInput.value = file
}

const toggleOpenCodeEditor = (): void => {
    openEditPanel.value = !openEditPanel.value
}

const handleCodeChange = (): void => {
    nodeCode.value = editor.value.getValue();
}

/** Sends the updated node config to the platform */
const debouncedUpdate = debounce(async () => {
    const nodeConfig = new NodeConfig({
        name: nodeName.value.trim(),
        validation: validation.value,
        isCodebase: isCodebase.value,
        codebaseType: nodeCodebaseType.value,
        code: nodeCode.value,
        zipInput: nodeZipInput.value,
        gitUrl: nodeGitUrl.value,
        gitTag: nodeGitTag.value,
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
    [nodeName, isCodebase, nodeCodebaseType, nodeCode, nodeZipInput, nodeGitUrl, nodeGitTag, validation],
    debouncedUpdate,
    {
        deep: true
    }
)

watch(nodeCodebaseType, () => {
    codebaseType.value = CODEBASE_TYPES_OPTIONS.find(e => e.value === nodeCodebaseType.value)
})

watch(component, () => {
    const nodeConfig = component.value?.metadata.customNodeConfig
    nodeName.value = nodeConfig.name
    isCodebase.value = nodeConfig.isCodebase
    nodeCodebaseType.value = nodeConfig.codebaseType
    nodeCode.value = nodeConfig.code
    nodeZipInput.value = nodeConfig.zipInput
    nodeGitUrl.value = nodeConfig.gitUrl
    nodeGitTag.value = nodeConfig.gitTag 
})

watch(theme, () => {
    setEditorTheme()
})
</script>

<template>
    <div id="panel">
        <dl-input
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

        <!-- <div class="margin-bottom">
            <dl-typography color="dl-color-medium" >Model Comparison Logic</dl-typography>
        </div>

        <div class="radio-container margin-bottom margin-top">
            <dl-radio padding="0" :value="false" v-model="isCodebase" label="Code Editor" />
            <dl-radio padding="0" :value="true" v-model="isCodebase" label="Codebase" />
        </div>

        <div class="margin-top" v-if="isCodebase">

            <div class="margin-bottom">
                <dl-select
                    :options="CODEBASE_TYPES_OPTIONS"
                    title="Codebase Type"
                    v-model="codebaseType"
                    @change="e => nodeCodebaseType = e.value"
                />
            </div>

            <div v-if="nodeCodebaseType === CODEBASE_TYPES.Git">
                <div class="margin-bottom">
                    <dl-input
                        without-root-padding
                        placeholder="Insert Git URL"
                        :error="!!nodeNameErrorMessage"
                        :error-message="nodeNameErrorMessage"
                        v-model="nodeGitUrl"
                        title="Git URL"
                        required
                        :disabled="readonly"
                    />
                </div>
                <div class="margin-bottom">
                    <dl-input
                        without-root-padding
                        placeholder="Insert Git tag"
                        :error="!!nodeNameErrorMessage"
                        :error-message="nodeNameErrorMessage"
                        v-model="nodeGitTag"
                        title="Git Tag"
                        :disabled="readonly"
                    />
                </div>

            </div>
            <div v-else >
                <dl-button dense size="s" style="margin-top: 8px" flat icon="icon-dl-upload" @click="openFileUpload" >Upload ZIP File</dl-button>
                <div class="margin-top"><dl-typography  v-if="nodeFileInput && nodeFileInput.name"> {{nodeFileInput.name}} </dl-typography></div>
            </div>

        </div>

        <div v-else class="margin-top">
            <div class="margin-bottom"><dl-button size="s" dense flat icon="icon-dl-edit" @click="toggleOpenCodeEditor" >Edit Logic Code</dl-button></div>

            <div :style="`height: 200px; display: ${openEditPanel ? '' : 'none'}; `">
                <div id="editor"></div>
            </div>

            <div class="requirements-text">
                <dl-typography>
                    Requirements (Optional) 
                </dl-typography>
                <dl-icon icon="icon-dl-info" color="dl-color-medium" /> 
            </div>

            <dl-button size="s" dense style="margin-top: 8px" flat icon="icon-dl-upload" @click="openRequirementsFileUpload" >Upload Requirements.txt</dl-button>
            <div class="margin-top"><dl-typography  v-if="nodeRequirementsFileInput && nodeRequirementsFileInput.name"> {{nodeRequirementsFileInput.name}} </dl-typography></div>

        </div> -->

    </div>
</template>

<style scoped>
.radio-container {
    display: flex;
    column-gap: 16px;
}

.margin-bottom {
    margin-bottom: 20px;
}

.margin-top {
    margin-top: 8px;
}

.requirements-text {
    display: flex;
    column-gap: 8px;
    align-items: center;
}

.ace_editor {
    height: 100%;
    width: 100%;
    position: relative;
}

</style>