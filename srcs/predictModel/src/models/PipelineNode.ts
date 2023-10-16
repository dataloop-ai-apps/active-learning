import { v4 } from 'uuid'

export interface ItemMetadata {
    key: string
    value: string
    type: string
}

export interface INodeConfig {
    name: string
    validation: ValidationDescriptor
}

/**
 * The node configuration JSON interface.
 *
 * @interface INodeConfigJSON
 * @typedef {Object} INodeConfigJSON
 * @property {string} name - The name of the node configuration.
 * @property {Object} body - The body of the node configuration.
 * @property {ValidationDescriptor} validation - The validation descriptor for the node configuration.
 */
export interface INodeConfigJSON {
    name: string
    body: {}
    validation: ValidationDescriptor
}

export interface Port {
    name: string
    action: string
    type: string
    portPercentage: number
}

const DEFAULT_VALUES = (): INodeConfig => ({
    name: 'Predict Node',
    validation: {
        valid: true,
        errors: []
    }
})

const NODE_DEFAULT_VALUES = {
    name: 'Predict Node',
    id: '',
    // TODO: rectify these values from Or or YAYA
    inputs: [],
    outputs: [],
    type: '',
    projectId:'',
    appId: '',
    metadata: {
        customNodeConfig : DEFAULT_VALUES()
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
            outputs:json.outputs,
            type: json.type,
            projectId:json.projectId,
            appId: json.appId,
            metadata: json.metadata,
            namespace: json.namespace,
        }
    }
}

export class NodeConfig implements INodeConfig {
    public name: string
    public validation: ValidationDescriptor

    constructor(init?: INodeConfig) {
        this.name = init?.name ?? NodeConfig.DefaultValues.name
        this.validation =
            init?.validation ?? NodeConfig.DefaultValues.validation
    }

    public static get DefaultValues() {
        return DEFAULT_VALUES()
    }

    public static fromJSON(json: Partial<NodeConfig>): INodeConfig {
        return {
            name: json?.name,
            validation: json?.validation
        }
    }

    public toJSON() {
        return {
            name: this.name,
            validation: this.validation,
        }
    }
}

export interface ValidationDescriptor {
    valid: boolean
    errors: { message: string; suggestion: string }[]
}
