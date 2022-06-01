import flashyLogo from '../assets/flashy.svg';
import flashyStroke from '../assets/flashy_stroke.svg';

import {
    Grid,
    Typography,
    Stack,
    Divider,
} from "lightning-ui/src/design-system/components";
import palette from "lightning-ui/src/design-system/theme/palette"


export default function Banner(props: any) {
    // @ts-ignore
    let grey = palette.grey[10]
    return (
        <Stack direction="column">
            <Stack direction={{ xs: 'column', sm: 'row' }} alignItems="center" spacing={3} bgcolor={grey} px={{ xs: 3, sm: 6}} py={3}>
                <img src={flashyLogo} alt="Flashy Logo" width="150px" height="150px"/>
                <Grid container spacing={2} alignItems="center">
                    <Grid item>
                        <img src={flashyStroke} alt="Flashy Stroke" width="150px"/>
                    </Grid>
                    <Grid item xs={12} sm>
                        <Typography variant="h2" fontSize="24px" fontWeight="600" lineHeight="20px">
                            The AutoML App
                        </Typography>
                    </Grid>
                    <Grid item xs={12}>
                        <Typography variant="body1">
                            Flashy is an auto-AI app that selects the best deep learning model for your image or text datasets. This app automatically uses state of the art models from Torchvision, TIMM and Hugging Face. This first version of the app is limited in scope and we encourage the community to help improve it!
                        </Typography>
                    </Grid>
                </Grid>
            </Stack>
            <Divider />
        </Stack>
    );
}
