import axios, {AxiosResponse} from 'axios';
import React from "react";
import { DataOptions, Format } from "../../types/data";
import {
    Grid,
    FormControl,
    Radio,
    RadioGroup,
    FormControlLabel,
    Typography, Stack
} from "lightning-ui/src/design-system/components";
import Widget from "./Widget";
import PillTextField from "../PillTextField";
import PillSelect from "../PillSelect";
import { useDropzone } from 'react-dropzone';
import PillButton from "../PillButton";
import CircularProgress from "@mui/material/CircularProgress";
import {Box} from "@mui/material";

export type DataConfigProps = {
    dataOptions: DataOptions;
    value: Map<string, any>;
    example: Map<string, any>;
    onChange: (config: Map<string, any>) => void;
    lightningState: any;
};

const DataConfig = React.forwardRef(
    (
        { dataOptions, value, example, onChange, lightningState }: DataConfigProps,
        ref,
    ) => {
        const [datasetFormat, setDatasetFormat] = React.useState('url');
        const [request, setRequest] = React.useState("");
        const [url, setUrl] = React.useState("" as null | string);
        const [uploadedDataset, setUploadedDataset] = React.useState('');
        const [dirs, setDirs] = React.useState([]);
        const [files, setFiles] = React.useState([]);

        const handleDatasetFormatChange = (event: any) => {
            setDatasetFormat(event.target.value);
        };

        let dataConfig = value;

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
                <Grid item xs={12} md={6} key={argument.name} sx={{display: (uploadedDataset? "initial": "none")}}>
                    <Widget
                        argument={argument}
                        value={dataConfig.get(argument.name)}
                        example={example.has(argument.name) && example.get(argument.name)}
                        onChange={(value: any) => onChange(new Map(dataConfig.set(argument.name, value)))}
                        files={files}
                        dirs={dirs}
                    />
                </Grid>
            )
        }

        function processResponse(response: AxiosResponse) {
            setUploadedDataset(response.data.path);

            axios.get(lightningState.vars.file_upload_url + "/listdirs/" + response.data.path).then((response) => {
                setDirs(response.data)
            });

            axios.get(lightningState.vars.file_upload_url + "/listfiles/" + response.data.path).then((response) => {
                setFiles(response.data)
            });
        }

        function startFileUpload(files: File[]) {
            const formData = new FormData();

            formData.append(
                "file",
                files[0],
                files[0].name
            );

            if (lightningState) {
                // TODO: Progress?
                setUploadedDataset("");
                setRequest(files[0].name);

                const headers={'Content-Type': "application/zip"}

                axios.post(lightningState.vars.file_upload_url + "/uploadzip/", formData, {"headers": headers}).then(processResponse);
            }
        }

        function startUrlUpload() {
            if (lightningState && url) {
                // TODO: Progress?
                setUploadedDataset("");
                setRequest(url.split("/").pop() as string)

                axios.post(lightningState.vars.file_upload_url + "/uploadurl/", {"url": url}).then(processResponse);
            }
        }

        const {
            getRootProps,
            getInputProps
        } = useDropzone({
            maxFiles:1,
            accept: {
                "application/zip": [],
            },
            onDropAccepted: startFileUpload,
        });

        let dataset = <></>

        if (request && !uploadedDataset) {
            dataset = <Stack direction="row" spacing={2}><CircularProgress size="24px" /><Typography variant="body2">Uploading {request}</Typography></Stack>
        } else if (request) {
            dataset = <Typography variant="h6">Select splits for {uploadedDataset}</Typography>
        }

        return (
            <>
                <Grid item xs={12}>
                    <FormControl>
                        <RadioGroup
                            name="dataset-format"
                            row
                            value={datasetFormat}
                            onChange={handleDatasetFormatChange}
                        >
                            <FormControlLabel value="url" control={<Radio />} label="From a URL" />
                            <FormControlLabel value="local" control={<Radio />} label="From this machine" />
                        </RadioGroup>
                    </FormControl>
                </Grid>
                <Grid item xs={12}>
                    {datasetFormat == "local"?
                        <Box {...getRootProps({ className: 'dropzone' })} py={3} sx={{color: "white", textAlign: "center", borderRadius: "42px", width: "100%", backgroundImage: theme => theme.palette.primary.gradient}}>
                            <input {...getInputProps()} />
                            <Typography variant="subtitle2">Drag and drop a zip file here, or click to browse</Typography>
                        </Box>:
                        <Stack direction="column" alignItems="flex-start" spacing={3}>
                            <PillTextField
                                helperText={"e.g " + example.get("url")}
                                label="Data URL"
                                onChange={setUrl}
                                fullWidth
                                statusText=""
                                value={dataConfig.get("url")}
                            />
                            <PillButton text="Upload" onClick={startUrlUpload}/>
                        </Stack>
                    }
                </Grid>
                <Grid item xs={12}>
                    {dataset}
                </Grid>
                <Grid item xs={12} sx={{display: (uploadedDataset? "initial": "none")}}>
                    <PillSelect
                        helperText=""
                        label="Format"
                        onChange={(value: any) => onChange(new Map([["url", dataConfig.get("url")], [ "target", value]]))}
                        options={dataOptions.formats.map(
                            (format: Format) => {return {label: format.name, value: format.label,}}
                        )}
                        fullWidth
                        statusText=""
                        value={(dataConfig.has("target") && dataConfig.get("target")) || example.get("target")}
                    />
                </Grid>
                { widgets }
            </>
        )
    }
)

export default DataConfig
