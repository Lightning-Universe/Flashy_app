import {Box, IconButton, Dialog, DialogContent, DialogTitle, Stack } from "lightning-ui/src/design-system/components";
import { Menu, MenuItem, ListItemIcon, ListItemText } from "@mui/material";
import React from "react";
import MoreHorizIcon from '@mui/icons-material/MoreHoriz';
import IosShareSharpIcon from '@mui/icons-material/IosShareSharp';
import PillTextField from "./PillTextField";
import PillTextLabel from "./PillTextLabel";

export type MoreMenuProps = {
    value: number | "failed" | "launching" | "stopped" | "succeeded";
    id: string;
    lightningState: any;
    updateLightningState: (newState: any) => void;
};

const MoreMenu = React.forwardRef(
    (
        { value, id, lightningState, updateLightningState }: MoreMenuProps,
        ref,
    ) => {
        const [checkpointDialogOpen, setCheckpointDialogOpen] = React.useState(false);
        const [anchorEl, setAnchorEl] = React.useState(null);

        const checkpointUrl = lightningState?.vars.checkpoints_server_url + "/file/" + id + "_checkpoint.pt";

        const handleClick = (event: any) => {
            setAnchorEl(event.currentTarget);
        };

        const handleClose = () => {
            setAnchorEl(null);
        };

        const open = Boolean(anchorEl);
        const menuId = open ? id : undefined;

        return (
            <div>
                <IconButton
                    id={menuId + "-button"}
                    aria-controls={menuId}
                    aria-haspopup="true"
                    onClick={handleClick}
                >
                    <MoreHorizIcon sx={{ fontSize: 16 }}/>
                </IconButton>
                <Menu
                    id={menuId}
                    open={open}
                    anchorEl={anchorEl}
                    onClose={handleClose}
                    anchorOrigin={{
                        vertical: 'bottom',
                        horizontal: 'left',
                    }}
                    transformOrigin={{
                        vertical: 'top',
                        horizontal: 'right',
                    }}
                >
                    <MenuItem onClick={() => {
                        setCheckpointDialogOpen(true);
                        handleClose();
                    }} disabled={value != "succeeded"}>
                        <ListItemIcon>
                            <IosShareSharpIcon sx={{ fontSize: 16 }} />
                        </ListItemIcon>
                        <ListItemText primary="Share checkpoint" />
                    </MenuItem>
                </Menu>
                <Dialog
                    open={checkpointDialogOpen}
                    onClose={() => setCheckpointDialogOpen(false)}
                    fullWidth={true}
                >
                    <DialogTitle text={"Checkpoint"} onClick={() => setCheckpointDialogOpen(false)}/>
                    <DialogContent>
                        <Stack direction={"column"} spacing={3}>
                            <PillTextLabel label="Here's your checkpoint URL" value={checkpointUrl}/>
                        </Stack>
                    </DialogContent>
                </Dialog>
            </div>
        )
    }
)

export default MoreMenu
