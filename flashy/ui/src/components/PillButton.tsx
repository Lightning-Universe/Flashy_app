import * as React from "react";

import { styled } from "@mui/material/styles";
import { Button } from "lightning-ui/src/design-system/components";

const PillButton = styled(Button)(({ theme }) => ({
    borderRadius: "42px",
}));

export default PillButton;
