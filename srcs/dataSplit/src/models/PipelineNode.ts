import { v4 } from 'uuid'

export interface Group {
    id: string
    name: string
    distribution: number
}

export interface ItemMetadata {
    key: string
    value: string
    type: string
}

export interface INodeConfig {
    name: string
    distributeEqually: boolean
    groups: Group[]
    itemMetadata?: boolean
    validation: ValidationDescriptor
    ports?: Port[]
}

/**
 * The node configuration JSON interface.
 *
 * @interface INodeConfigJSON
 * @typedef {Object} INodeConfigJSON
 * @property {string} name - The name of the node configuration.
 * @property {Object} body - The body of the node configuration.
 * @property {boolean} body.distributeEqually - Indicates whether the groups should be distributed equally.
 * @property {Group[]} body.groups - An array of groups associated with the node configuration.
 * @property {ItemMetadata} [body.itemMetadata] - The metadata associated with the node configuration.
 * @property {ValidationDescriptor} validation - The validation descriptor for the node configuration.
 * @property {Port[]} [ports] - An array of ports associated with the node configuration.
 */
export interface INodeConfigJSON {
    name: string
    body: {
        distributeEqually: boolean
        groups: Group[]
        itemMetadata?: boolean
    }
    validation: ValidationDescriptor
    ports?: Port[]
}

export interface Port {
    name: string
    action: string
    type: string
    portPercentage: number
}

const DEFAULT_VALUES = (): INodeConfig => ({
    name: 'Data Split',
    groups: [
        { id: v4(), name: 'group_1', distribution: 50 },
        { id: v4(), name: 'group_2', distribution: 50 }
    ],
    distributeEqually: true,
    itemMetadata: false,
    validation: {
        valid: true,
        errors: []
    }
})

const NODE_DEFAULT_VALUES = {
    name: 'Data Split',
    id: '',
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
 * @property {boolean} distributeEqually - Indicates whether the data should be distributed equally between the groups.
 * @property {Group[]} groups - An array of groups associated with the node configuration.
 * @property {ItemMetadata} [itemMetadata] - The item metadata associated with the node configuration.
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
    actions?: string[]
    portPercentage?: number
    type: string
    defaultValue?: string | number | boolean | Dictionary | null
    nodeId?: string
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
        this.inputs = init?.inputs ?? NODE_DEFAULT_VALUES.inputs
        this.metadata = init?.metadata ?? NODE_DEFAULT_VALUES.metadata
        this.outputs = [{
                portId: init?.outputs[0]?.portId ?? v4(),
                actions: this.metadata.customNodeConfig.groups.filter((dict) => dict.name.trim() !== '').map(element => { return element.name }) ?? [],
                name: 'item',
                nodeId: this.id,
                type: 'Item'
            }
        ]
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
    public distributeEqually: boolean
    public groups: Group[]
    public itemMetadata?: boolean
    public validation: ValidationDescriptor

    constructor(init?: INodeConfig) {
        this.name = init?.name ?? NodeConfig.DefaultValues.name
        this.distributeEqually =
            init?.distributeEqually ??
            NodeConfig.DefaultValues.distributeEqually
        this.groups = init?.groups ?? NodeConfig.DefaultValues.groups
        this.itemMetadata =
            init?.itemMetadata ?? NodeConfig.DefaultValues.itemMetadata
        this.validation =
            init?.validation ?? NodeConfig.DefaultValues.validation
    }

    public static get DefaultValues() {
        return DEFAULT_VALUES()
    }

    public get ports(): Port[] {
        return this.groups.map((group) => {
            return {
                action: group.name,
                name: 'item',
                type: 'Item',
                portPercentage: group.distribution
            }
        })
    }

    public static fromJSON(json: Partial<NodeConfig>): INodeConfig {
        return {
            name: json?.name,
            distributeEqually: json?.distributeEqually,
            groups: json?.groups,
            itemMetadata: json?.itemMetadata,
            validation: json?.validation
        }
    }

    public toJSON() {
        return {
            name: this.name,
            distributeEqually: this.distributeEqually,
            groups: this.groups,
            itemMetadata: this.itemMetadata ?? false,
            validation: this.validation,
            ports: this.ports
        }
    }
}

export interface ValidationDescriptor {
    valid: boolean
    errors: { message: string; suggestion: string }[]
}
