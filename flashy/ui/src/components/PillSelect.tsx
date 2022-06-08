import * as React from "react";

import { styled } from "@mui/material/styles";
import { Select } from "lightning-ui/src/design-system/components";

const PillSelect = styled(Select)(({ theme }) => ({
    [`&>div`]: {
        borderRadius: "20px !important",
    },
}));

export default PillSelect;
