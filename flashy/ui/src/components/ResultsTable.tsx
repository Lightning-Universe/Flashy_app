import React, { ReactNode } from 'react';

import {
    Typography,
    Stack,
    Table,
} from "lightning-ui/src/design-system/components";
import RunProgress from "./RunProgress";


function ResultRow(run: { id: string, task: string, model_config: any, data_config: any }, progress: number | "failed" | "launching" | "stopped", lightningState: any, updateLightningState: (newState: any) => void, monitor?: number): ReactNode[] {
    return [
        run.id,
        <RunProgress value={progress} id={run.id} lightningState={lightningState} updateLightningState={updateLightningState}/>,
        ...Object.entries(run.model_config).map(
            (value: any)  => value[1]
        ),
        monitor? monitor: "-",
    ]
}


export default function ResultsTable(props: {sweepId: string, results: any, lightningState: any, updateLightningState: (newState: any) => void}) {
    if (props.lightningState) {
        if (Object.entries(props.results).length > 0) {
            const rows = Object.entries(props.results).map(
                (value: any) => ResultRow(value[1].run, value[1].progress, props.lightningState, props.updateLightningState, value[1].monitor)
            )

            const header = ["ID", "Progress", ...Object.entries((Object.entries(props.results) as any[])[0][1].run.model_config).map((value: any) => value[0]), "Performance"]

            return (
                <Stack direction={"column"} spacing={3}>
                    <Typography variant="h6">Sweep {props.sweepId}</Typography>
                    <Table header={header} rows={rows}/>
                </Stack>
            )
        }
    }

    return (<></>)
}
