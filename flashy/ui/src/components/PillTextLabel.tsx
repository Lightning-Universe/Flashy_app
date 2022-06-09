import * as React from "react";

import { styled } from "@mui/material/styles";
import PillTextField from "./PillTextField";
import { TextFieldProps } from "lightning-ui/src/design-system/components/text-field";

const PillTextFieldDisabledOverride = styled(PillTextField)(({ theme }) => ({
    [`&.Mui-disabled .MuiOutlinedInput-input`]: {
        backgroundColor: "white",
        color: theme.palette.grey[100],
        "-webkit-text-fill-color": theme.palette.grey[100],
    },
}));

const PillTextLabel = React.forwardRef(
    (
        props: Omit<TextFieldProps, "onChange" | "disabled">,
        ref,
    ) => {
        return (
            <PillTextFieldDisabledOverride {...props} disabled onChange={() => null}/>
        )
    }
)

export default PillTextLabel;
