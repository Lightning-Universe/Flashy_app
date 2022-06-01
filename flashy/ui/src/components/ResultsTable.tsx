import React, { ReactNode } from 'react';
import { ReactComponent as GreenTick } from '../assets/green_tick.svg';
import cloneDeep from "lodash/cloneDeep";

import InfoIcon from '@mui/icons-material/Info';

import {
    Grid,
    Typography,
    Stack,
    Box,
    SvgIcon,
    Table,
} from "lightning-ui/src/design-system/components";
import { useLightningState } from "../hooks/useLightningState";

import CircularProgress  from "@mui/material/CircularProgress";
import {DataOptions, Demo} from "../types/data";
import DataConfig from './data/DataConfig';
import PillButton from './PillButton';
import PillTextField from "./PillTextField";
import PillSelect from "./PillSelect";
import useSelectedTabState from "../hooks/useSelectedTabState";


function ResultRow(run: { id: number, task: string, model_config: any, data_config: any }, progress: number | "failed" | "completed", monitor?: number): ReactNode[] {
    return [
        run.id,
        // TODO: Progress bar / status buttons
        progress,
        ...Object.entries(run.model_config).map(
            (value: any)  => value[1]
        ),
        monitor? monitor: "-",
    ]
}


export default function ResultsTable(props: {lightningState: any, updateLightningState: (newState: any) => void}) {
    if (props.lightningState) {
        const results = props.lightningState.flows.hpo.vars.results;

        if (Object.entries(results).length > 0) {
            const rows = Object.entries(results).map(
                (value: any) => ResultRow(value[1].run, value[1].progress, value[1].monitor)
            )

            const header = ["ID", "Progress", ...Object.entries((Object.entries(results) as any[])[0][1].run.model_config).map((value: any) => value[0]), "Performance"]

            return (
                <Stack direction={"column"} spacing={3} px={{xs: 6, sm: 12, md: 18}} py={6}>
                    <Typography variant="h6">Results</Typography>
                    <Table header={header} rows={rows}/>
                </Stack>
            )
        }
    }

    return (<></>)
}
