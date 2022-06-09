import * as React from "react";

import {IconButton, Typography,} from "lightning-ui/src/design-system/components";
import Status, {StatusEnum} from "lightning-ui/src/shared/components/Status";
import Box from "@mui/material/Box";
import LinearProgress, {linearProgressClasses} from "@mui/material/LinearProgress";
import CancelIcon from '@mui/icons-material/Cancel';
import {styled} from "@mui/material/styles";
import cloneDeep from "lodash/cloneDeep";

const BorderLinearProgress = styled(LinearProgress)(({ theme }) => ({
    height: 8,
    borderRadius: 6,
    [`&.${linearProgressClasses.colorPrimary}`]: {
        backgroundColor: theme.palette.grey[theme.palette.mode === "light" ? 200 : 800],
    },
    [`& .${linearProgressClasses.bar}`]: {
        borderRadius: 6,
        backgroundColor: theme.palette.primary['main'],
    },
}));

export type RunProgressProps = {
    value: number | "failed" | "launching" | "stopped";
    id: string;
    lightningState: any;
    updateLightningState: (newState: any) => void;
};

const RunProgress = React.forwardRef(
    (
        { value, id, lightningState, updateLightningState }: RunProgressProps,
        ref,
    ) => {
        function stopRun() {
            if (lightningState) {
                // Create and send new state
                const newLightningState = cloneDeep(lightningState);
                newLightningState.flows.hpo.vars.stopped_run = id;

                updateLightningState(newLightningState);
            }
        }

        if (value == "launching") {
            return (
                <BorderLinearProgress/>
            );
        } else if (value == "failed") {
            return (
                <Status status={StatusEnum.FAILED}/>
            )
        } else if (value == "stopped") {
            return (
                <Status status={StatusEnum.STOPPED}/>
            )
        } else {
            value = Math.round(value * 100)

            if (value >= 100) {
                return (
                    <Status status={StatusEnum.SUCCEEDED}/>
                )
            }

            return (
                <Box sx={{display: "flex", alignItems: "center", height:"20px"}}>
                    <Box sx={{width: "100%", mr: 1}}>
                        <BorderLinearProgress variant="determinate" value={value}/>
                    </Box>
                    <Box sx={{minWidth: 35}}>
                        <Typography variant="body2" color="text.secondary">{`${Math.round(value)}%`}</Typography>
                    </Box>
                    <Box>
                        <IconButton onClick={stopRun}><CancelIcon sx={{ fontSize: 16 }}/></IconButton>
                    </Box>
                </Box>
            );
        }
    }
)

export default RunProgress;
