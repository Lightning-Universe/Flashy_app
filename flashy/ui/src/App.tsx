import { useEffect } from "react";

import { QueryClient, QueryClientProvider } from "react-query";
import { BrowserRouter } from "react-router-dom";

// import ErrorPanel from "components/ErrorPanel";
// import HyperparameterSummary from "components/HyperparameterSummary";
// import Launcher from "components/Launcher";
// import ProgressBarGroup from "components/ProgressBarGroup";
import Configurator from "components/Configurator"
import Banner from "components/Banner"
import {
  Breadcrumbs,
  Card,
  CardContent,
  CardHeader,
  Grid,
  SnackbarProvider,
  Stack,
  useSnackbar,
} from "lightning-ui/src/design-system/components";
import ThemeProvider from "lightning-ui/src/design-system/theme";

// import ExecutionSummary from "./components/ExecutionSummary";
import { useLightningState } from "./hooks/useLightningState";

const queryClient = new QueryClient();

function AppContainer() {

  // const { enqueueSnackbar } = useSnackbar();
  // const exception_message = lightningState?.flows.script_orchestrator.works.script_runner?.vars?.exception_message;
  // useEffect(() => {
  //   if (exception_message) {
  //     enqueueSnackbar({
  //       title: "The script failed to complete",
  //       severity: "error",
  //       children: "See the error message",
  //     });
  //   }
  // }, [exception_message]);

  return (
      <Stack order="column">
        <Banner />
        <Configurator />
      </Stack>
      // <Stack sx={{ height: "100vh", margin: "auto" }}>
      // </Stack>
  );
}

function App() {
  return (
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <SnackbarProvider>
            <AppContainer />
          </SnackbarProvider>
        </BrowserRouter>
      </QueryClientProvider>
    </ThemeProvider>
  );
}

export default App;
