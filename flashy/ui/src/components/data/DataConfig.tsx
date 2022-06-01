import React, { useState } from "react";
import { DataOptions, Format } from "../../types/data";
import {Grid} from "lightning-ui/src/design-system/components";
import Widget from "./Widget";
import PillTextField from "../PillTextField";
import PillSelect from "../PillSelect";

export type DataConfigProps = {
    dataOptions: DataOptions;
    value: Map<string, any>;
    onChange: (config: Map<string, any>) => void;
};

const DataConfig = React.forwardRef(
    (
        { dataOptions, value, onChange }: DataConfigProps,
        ref,
    ) => {
        let dataConfig = value

        // Find the index of the Format object
        let formatIndex = dataOptions.formats.findIndex((format: Format) => format.name == value.get("target"))

        // Trigger a refresh with the new format if it wasn't set
        if (formatIndex == -1) {
            formatIndex = 0
            dataConfig = new Map([["url", dataConfig.get("url")], ["target", dataOptions.formats[formatIndex].name]])
            onChange(dataConfig)
        }

        let format = dataOptions.formats[formatIndex]

        let widgets = [];
        for (let i = 0; i < format.arguments.length; i++)  {
            let argument = format.arguments[i]
            widgets.push(
                <Grid item xs={12} sm={6} key={argument.name}>
                    <Widget
                        argument={argument}
                        value={dataConfig.get(argument.name)}
                        onChange={(value: any) => onChange(new Map(dataConfig.set(argument.name, value)))}
                    />
                </Grid>
            )
        }

        return (
            <>
                <Grid item xs={12} sm={6}>
                    <PillSelect
                        helperText=""
                        label="Format"
                        onChange={(value: any) => onChange(new Map([["url", dataConfig.get("url")], [ "target", value]]))}
                        options={dataOptions.formats.map(
                            (format: Format) => {return {label: format.name, value: format.label,}}
                        )}
                        fullWidth
                        statusText=""
                        value={dataConfig.get("target")}
                    />
                </Grid>
                <Grid item xs={12} sm={6}>
                    <PillTextField
                        helperText=""
                        label="Data URL"
                        onChange={(value: any) => onChange(new Map(dataConfig.set("url", value)))}
                        fullWidth
                        statusText=""
                        value={dataConfig.get("url")}
                    />
                </Grid>
                { widgets }
            </>
        )
    }
)

export default DataConfig
