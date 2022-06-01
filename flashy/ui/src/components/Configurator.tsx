import React from 'react';
import { ReactComponent as GreenTick } from '../assets/green_tick.svg';
import cloneDeep from "lodash/cloneDeep";

import InfoIcon from '@mui/icons-material/Info';

import {
    Grid,
    Typography,
    Stack,
    Box,
    SvgIcon,
} from "lightning-ui/src/design-system/components";
import { useLightningState } from "../hooks/useLightningState";

import CircularProgress  from "@mui/material/CircularProgress";
import {DataOptions, Demo} from "../types/data";
import DataConfig from './data/DataConfig';
import PillButton from './PillButton';
import PillTextField from "./PillTextField";
import PillSelect from "./PillSelect";
import useSelectedTabState from "../hooks/useSelectedTabState";



const loadingOptions: DataOptions[] = [
    {
        task: "image_classification",
        label: "Image Classification",
        formats: [
            {
                name: "from_folders",
                label: "Folders",
                arguments: [
                    {name: "train_folder", label: "Train Folder", type: "string"},
                    {name: "val_folder", label: "Validation Folder", type: "string"},
                ],
            },
            {
                name: "from_csv",
                label: "CSV",
                arguments: [
                    {name: "input_field", label: "Input Field", type: "string"},
                    {name: "target_fields", label: "Target Field", type: "string"},
                    {name: "train_file", label: "Train CSV File", type: "string"},
                    {name: "train_images_root", label: "Train Image Folder", type: "string"},
                    {name: "val_file", label: "Validation CSV File", type: "string"},
                    {name: "val_images_root", label: "Validation Image Folder", type: "string"},
                ],
            },
        ],
    },
    {
        task: "text_classification",
        label: "Text Classification",
        formats: [
            {
                name: "from_csv",
                label: "CSV",
                arguments: [
                    {name: "input_field", label: "Input Field", type: "string"},
                    {name: "target_fields", label: "Target Field", type: "string"},
                    {name: "train_file", label: "Train CSV File", type: "string"},
                    {name: "val_file", label: "Validation CSV File", type: "string"},
                ],
            },
        ],
    }
]


const Demos: Demo[]  = [
    {
        name: "ants_bees",
        label: "ants & bees detector",
        task: "image_classification",
        config: new Map([
            ["url", "https://pl-flash-data.s3.amazonaws.com/hymenoptera_data.zip"],
            ["target", "from_folders"],
            ["train_folder", "hymenoptera_data/train/"],
            ["val_folder", "hymenoptera_data/val/"],
        ])
    },
    {
        name: "movie_reviews",
        label: "movie review sentiment analyser",
        task: "text_classification",
        config: new Map([
            ["url", "https://pl-flash-data.s3.amazonaws.com/imdb.zip"],
            ["target", "from_csv"],
            ["input_field", "review"],
            ["target_fields", "sentiment"],
            ["train_file", "imdb/train.csv"],
            ["val_file", "imdb/valid.csv"],
        ])
    }
]


export default function Configurator(props: {lightningState: any, updateLightningState: (newState: any) => void}) {
    const { setSelectedTab } = useSelectedTabState();

    const ready = props.lightningState?.flows.hpo.vars.ready;

    const [demo, setDemo] = React.useState('ants_bees');
    const [task, setTask] = React.useState('image_classification');
    const [taskPrompt, setTaskPrompt] = React.useState('');
    const [modelType, setModelType] = React.useState('demo');
    const [targetPerformance, setTargetPerformance] = React.useState('low');
    const [showLaunchingSpinner, setShowLaunchingSpinner] = React.useState(false);

    const [dataConfig, setDataConfig] = React.useState(Demos[0].config);

    function startTraining() {
        setShowLaunchingSpinner(true);
        if (props.lightningState) {
            // HACK: Ensures that ready is false
            props.lightningState.flows.hpo.vars.ready = false

            // Create and send new state
            const newLightningState = cloneDeep(props.lightningState);
            newLightningState.flows.hpo.vars.start = true;
            newLightningState.flows.hpo.vars.selected_task = task;
            newLightningState.flows.hpo.vars.data_config = Object.fromEntries(dataConfig);
            newLightningState.flows.hpo.vars.model = modelType;
            newLightningState.flows.hpo.vars.performance = targetPerformance;

            props.updateLightningState(newLightningState);
        }
    }

    function setDemoDataConfig(value: any) {
        setDemo(value)
        let demoIndex = Demos.findIndex((demo: Demo) => demo.name == value)
        setTask(Demos[demoIndex].task)
        setDataConfig(Demos[demoIndex].config)
    }

    return (
        <>
            <Box display={!showLaunchingSpinner? "initial": "none"}>
                <Grid container spacing={3} px={{xs: 6, sm: 12, md: 18}} py={6}>
                    <Grid item xs={12}>
                        <Typography variant="h6">Get started</Typography>
                    </Grid>
                    <Grid item xs={12} md={6}>
                        <PillSelect
                            helperText=""
                            label="Choose a pre-configured demo"
                            onChange={setDemoDataConfig}
                            options={Demos.map((demo: Demo) => {return {label: demo.name, value: demo.label}})}
                            fullWidth
                            statusText=""
                            value={demo}
                        />
                    </Grid>
                    <Grid item xs={12} md={6}>
                        <PillTextField
                            helperText=""
                            label="Or describe what you want to build"
                            onChange={setTaskPrompt as (value: any) => void}
                            fullWidth
                            statusText=""
                            value={taskPrompt}
                            disabled={true}
                        />
                    </Grid>
                    <Grid item xs={12}>
                        <Typography variant="h6">Load your data</Typography>
                    </Grid>
                    <DataConfig dataOptions={loadingOptions[loadingOptions.findIndex((dataOptions: DataOptions) => dataOptions.task == task)]} value={dataConfig} onChange={setDataConfig}/>
                    <Grid item xs={12}>
                        <Typography variant="h6">Configure your sweep</Typography>
                    </Grid>
                    <Grid item xs={12} md={6}>
                        <PillSelect
                            helperText=""
                            label="Model type"
                            onChange={setModelType as (value: any) => void}
                            options={[
                                {
                                    label: "demo",
                                    value: "Demo",
                                },
                                {
                                    label: "average",
                                    value: "Average",
                                },
                                {
                                    label: "sota",
                                    value: "State-of-the-art",
                                },
                            ]}
                            fullWidth
                            statusText=""
                            value={modelType}
                        />
                    </Grid>
                    <Grid item xs={12} md={6}>
                        <PillSelect
                            helperText=""
                            label="Target performance"
                            onChange={setTargetPerformance as (value: any) => void}
                            options={[
                                {
                                    label: "low",
                                    value: "Low",
                                },
                                {
                                    label: "medium",
                                    value: "Medium",
                                },
                                {
                                    label: "high",
                                    value: "High",
                                },
                            ]}
                            fullWidth
                            statusText=""
                            value={targetPerformance}
                        />
                    </Grid>
                    <Grid item xs={12}>
                        <Stack direction="row" spacing={2} alignItems="center">
                            <PillButton text="Start training!" onClick={startTraining}/>
                            {props.lightningState?.flows.hpo.vars.has_run? [
                                (<Typography variant="subtitle2">
                                    <Stack direction="row" alignItems="center">
                                        <InfoIcon color="primary" fontSize="inherit"/>
                                        <span style={{lineHeight: 1, marginLeft: "0.25em"}}>Your current run will be deleted</span>
                                    </Stack>
                                </Typography>),
                            ]: []}
                        </Stack>
                    </Grid>
                </Grid>
            </Box>
            <Box display={showLaunchingSpinner? "initial": "none"} py={12}>
                <Stack direction="column" alignItems="center">
                    <CircularProgress thickness={1} size="96px" sx={{my: 3, display: (!ready? "initial": "none")}} />
                    <SvgIcon sx={{width: "96px", height: "96px", my: 3, display: (ready? "initial": "none")}} viewBox="0 0 96 96">
                        <GreenTick />
                    </SvgIcon>
                    <Typography variant="h5" mb={1}>{ready? "Ready": "Launching..."}</Typography>
                    <Typography variant="body1" mb={3}>Hang tight!</Typography>
                    <Stack direction="row" spacing={3}>
                        <PillButton text="View results" disabled={!ready} onClick={() => setSelectedTab(1)}/>
                        <PillButton text="Start over" color="grey" onClick={() => setShowLaunchingSpinner(false)}/>
                    </Stack>
                </Stack>
            </Box>
        </>
    )
}
