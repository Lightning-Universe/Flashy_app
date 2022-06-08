import React from "react";
import { Argument } from "../../types/data";
import PillTextField from "../PillTextField";
import PillSelect from "../PillSelect";

export type WidgetProps = {
    argument: Argument;
    value: string;
    onChange: (value: any) => void;
    example?: string;
    files: string[];
    dirs: string[];
};

const Widget = React.forwardRef(
    (
        { argument, value, onChange, example, files, dirs }: WidgetProps,
        ref,
    ) => {
        switch (argument.type) {
            case "string":
                return (
                    <PillTextField
                        helperText={example? "e.g. " + example: " "}
                        label={argument.label}
                        onChange={(value: any) => onChange(value)}
                        fullWidth
                        statusText=""
                        value={value}
                    />
                )
            case "file":
                return (
                    <PillSelect
                        helperText={example? "e.g. " + example: " "}
                        label={argument.label}
                        onChange={(value: any) => onChange(value)}
                        options={files.map((file: string) => {return {label: file, value: file}})}
                        fullWidth
                        statusText=""
                        value={value}
                    />
                )
            case "folder":
                return (
                    <PillSelect
                        helperText={example? "e.g. " + example: " "}
                        label={argument.label}
                        onChange={(value: any) => onChange(value)}
                        options={dirs.map((dir: string) => {return {label: dir, value: dir}})}
                        fullWidth
                        statusText=""
                        value={value}
                    />
                )
        }
    }
)

export default Widget
