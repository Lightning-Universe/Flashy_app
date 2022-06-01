import React from "react";
import { Argument } from "../../types/data";
import PillTextField from "../PillTextField";

export type WidgetProps = {
    argument: Argument;
    value: string;
    onChange: (value: any) => void;
};

const Widget = React.forwardRef(
    (
        { argument, value, onChange }: WidgetProps,
        ref,
    ) => {
        switch (argument.type) {
            case "string":
                return (
                    <PillTextField
                        helperText=""
                        label={argument.label}
                        onChange={(value: any) => onChange(value)}
                        fullWidth
                        statusText=""
                        value={value}
                    />
                )
        }
    }
)

export default Widget
