import { v4 } from 'uuid'

export interface ItemMetadata {
    key: string
    value: string
    type: string
}

export enum CODEBASE_TYPES {
    Git = 'GIT',
    Zip = 'ZIP',
}

export const CODEBASE_TYPES_OPTIONS = [
    { label: 'Git', value: CODEBASE_TYPES.Git },
    { label: 'ZIP File', value: CODEBASE_TYPES.Zip }
]

export interface INodeConfig {
    name: string,
    isCodebase: boolean
    codebaseType?: CODEBASE_TYPES | null,
    code: string,
    zipInput: null | File,
    gitUrl: string,
    gitTag: string,
    validation: ValidationDescriptor,
}

/**
 * The node configuration JSON interface.
 *
 * @interface INodeConfigJSON
 * @typedef {Object} INodeConfigJSON
 * @property {string} name - The name of the node configuration.
 * @property {Object} body - The body of the node configuration.
 * @property {boolean} body.isCodebase - whether using codebase or not.
 * @property {CODEBASE_TYPES} body.codebaseType - which comparison logic to be used
 * @property {string} body.code - actual code to be executed
 * @property {null} body.zipInput - zip file for the code logic
 * @property {string} body.gitUrl - git url for the code logic
 * @property {string} body.gitTag - git tag for the code logic
 * @property {ValidationDescriptor} validation - The validation descriptor for the node configuration.
 */
export interface INodeConfigJSON {
    name: string
    body: {
        isCodebase: boolean
        codebaseType: CODEBASE_TYPES | null,
        code: string,
        zipInput: null | File,
        gitUrl: string,
        gitTag: string,
    }
    validation: ValidationDescriptor
}

export interface Port {
    name: string
    action: string
    type: string
    portPercentage: number
}

const DEFAULT_VALUES = (): INodeConfig => ({
    name: 'Compare Models',
    isCodebase: false,
    codebaseType: CODEBASE_TYPES.Git,
    code: "",
    zipInput: null,
    gitUrl: "",
    gitTag: "",
    validation: {
        valid: true,
        errors: []
    }
})

const NODE_DEFAULT_VALUES = {
    name: 'Compare Models',
    id: '',
    // TODO: rectify these values from Or or YAYA
    inputs: [],
    outputs: [],
    type: '',
    projectId: '',
    appId: '',
    metadata: {
        customNodeConfig: DEFAULT_VALUES()
    },
    namespace: {
        projectName: "",
        serviceName: "",
        functionName: "",
        moduleName: "",
        packageName: "",
    }
}

/**
 * Represents a Node Configuration.
 * @class
 * @implements INodeConfig
 * @property {string} name - The name of the node configuration.
 * @property {string} isCodebase - whether using codebase or not.
 * @property {string} codebaseType - which comparison logic to be used
 * @property {string} code - actual code to be executed
 * @property {string} zipInput - zip file for the code logic
 * @property {string} gitUrl - git url for the code logic
 * @property {string} gitTag - git tag for the code logic
 * @property {ValidationDescriptor} validation - The validation for the node.
 */

export type Dictionary = { [key: string]: any }

export interface NodeNamespace {
    projectName: string
    serviceName: string
    functionName: string
    moduleName?: string
    packageName?: string
}

export interface IODescriptor {
    name: string
    portId?: string
    displayName?: string
    color?: string
    actionIcon?: string
    action?: string
    portPercentage?: number
    type: string
    defaultValue?: string | number | boolean | Dictionary | null
}

export class NodeDescriptor {
    public namespace: NodeNamespace;
    public inputs: IODescriptor[];
    public outputs: IODescriptor[];
    public type: string;
    public projectId?: string;
    public name: string;
    public appId?: string;
    public metadata: Dictionary
    public id: string

    constructor(init?: NodeDescriptor) {
        this.id = init?.id ?? NODE_DEFAULT_VALUES.id
        this.name = init?.name ?? NODE_DEFAULT_VALUES.name
        // TODO: fix this. call about this input and output set. Also get the value of icons
        this.inputs = init?.inputs ? init?.inputs : NODE_DEFAULT_VALUES.inputs
        this.outputs = init?.outputs ? init?.outputs : NODE_DEFAULT_VALUES.outputs
        this.metadata = init?.metadata ?? NODE_DEFAULT_VALUES.metadata
        this.type = init?.type ?? NODE_DEFAULT_VALUES.type
        this.projectId = init?.projectId ?? NODE_DEFAULT_VALUES.projectId
        this.appId = init?.appId ?? NODE_DEFAULT_VALUES.appId
        this.namespace = init?.namespace ?? NODE_DEFAULT_VALUES.namespace
    }

    public static fromJSON(json: Partial<NodeDescriptor>): NodeDescriptor {
        return {
            id: json.id,
            name: json.name,
            inputs: json.inputs,
            outputs: json.outputs,
            type: json.type,
            projectId: json.projectId,
            appId: json.appId,
            metadata: json.metadata,
            namespace: json.namespace,
        }
    }
}

export class NodeConfig implements INodeConfig {
    public name: string
    public itemMetadata?: boolean
    public validation: ValidationDescriptor
    public isCodebase: boolean
    public codebaseType: CODEBASE_TYPES | null
    public code: string
    public zipInput: File | null
    public gitUrl: string
    public gitTag: string

    constructor(init?: INodeConfig) {
        this.name = init?.name ?? NodeConfig.DefaultValues.name
        this.isCodebase = init?.isCodebase ?? NodeConfig.DefaultValues.isCodebase
        this.codebaseType = init?.codebaseType ?? NodeConfig.DefaultValues.codebaseType
        this.code = init?.code ?? NodeConfig.DefaultValues.code
        this.zipInput = init?.zipInput ?? NodeConfig.DefaultValues.zipInput
        this.gitUrl = init?.gitUrl ?? NodeConfig.DefaultValues.gitUrl
        this.gitTag = init?.gitTag ?? NodeConfig.DefaultValues.gitTag
        this.validation =
            init?.validation ?? NodeConfig.DefaultValues.validation
    }

    public static get DefaultValues() {
        return DEFAULT_VALUES()
    }

    public static fromJSON(json: Partial<NodeConfig>): INodeConfig {
        return {
            name: json?.name,
            isCodebase: json?.isCodebase,
            codebaseType: json?.codebaseType,
            code: json?.code,
            zipInput: json?.zipInput,
            gitUrl: json?.gitUrl,
            gitTag: json?.gitTag,
            validation: json?.validation
        }
    }

    public toJSON() {
        return {
            name: this.name,
            validation: this.validation,
            isCodebase: this.isCodebase,
            codebaseType: this.codebaseType,
            code: this.code,
            zipInput: this.zipInput,
            gitUrl: this.gitUrl,
            gitTag: this.gitTag,
        }
    }
}

export interface ValidationDescriptor {
    valid: boolean
    errors: { message: string; suggestion: string }[]
}
