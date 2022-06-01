import * as React from "react";

import { styled } from "@mui/material/styles";
import { TextField } from "lightning-ui/src/design-system/components";

const PillTextField = styled(TextField)(({ theme }) => ({
    borderRadius: "20px",
}));

export default PillTextField;
