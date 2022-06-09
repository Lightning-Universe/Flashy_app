import { Stack } from 'lightning-ui/src/design-system/components';
import React from 'react';

import ResultsTable from "./ResultsTable";


export default function ResultsTableGroup(props: {lightningState: any, updateLightningState: (newState: any) => void}) {
    if (props.lightningState) {
        let results = props.lightningState.flows.hpo.vars.results;
        console.log(results)
        results = Object.entries(results).sort((a: [string, any], b: [string, any]) => (+a[0]) - (+b[0]));
        results = results.map(
            ( entry: [string, any] ) => <ResultsTable sweepId={entry[0]} results={entry[1]} lightningState={props.lightningState} updateLightningState={props.updateLightningState}/>
        )
        console.log(results)
        return (
            <Stack direction="column" spacing={6} px={{xs: 6, sm: 12, md: 18}} py={6}>
                {results}
            </Stack>
        )
    }
    return <></>
}
