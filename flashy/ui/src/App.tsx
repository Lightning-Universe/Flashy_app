import { QueryClient, QueryClientProvider } from "react-query";
import { BrowserRouter } from "react-router-dom";

import Configurator from "components/Configurator"
import Banner from "components/Banner"
import {
  SnackbarProvider,
  Stack,
} from "lightning-ui/src/design-system/components";
import ThemeProvider from "lightning-ui/src/design-system/theme";
import Tabs, { TabItem } from "components/Tabs";
import React from "react";
import useSelectedTabState, { SelectedTabProvider } from "hooks/useSelectedTabState";
import { useLightningState } from "hooks/useLightningState";
import ResultsTableGroup from "./components/ResultsTableGroup";

const queryClient = new QueryClient();

function Run(props: {lightningState: any, updateLightningState: (newState: any) => void}) {
  return (
      <Stack order="column">
        <Banner />
        <Configurator lightningState={props.lightningState} updateLightningState={props.updateLightningState}/>
      </Stack>
  );
}

function Results(props: {lightningState: any, updateLightningState: (newState: any) => void}) {
    return (
        <Stack order="column">
            <Banner />
            <ResultsTableGroup lightningState={props.lightningState} updateLightningState={props.updateLightningState}/>
        </Stack>
    );
}

function AppTabs() {
    const { lightningState, updateLightningState } = useLightningState();
    const { selectedTab, setSelectedTab } = useSelectedTabState();

    const tabItems: TabItem[] = [
        { title: "RUN", content: <Run lightningState={lightningState} updateLightningState={updateLightningState}/> },
        { title: "RESULTS", content: <Results lightningState={lightningState} updateLightningState={updateLightningState}/> },
    ];

    return (
        <Tabs selectedTab={selectedTab} onChange={setSelectedTab} tabItems={tabItems} sxTabs={{width: "100%", backgroundColor: "white", paddingX: 2, top: 0, position: "fixed", zIndex: 1000}} sxContent={{paddingTop: 0, paddingBottom: 6, marginTop: "48px"}}/>
    )
}

function App() {
    return (
        <ThemeProvider>
            <QueryClientProvider client={queryClient}>
                <BrowserRouter>
                    <SnackbarProvider>
                        <SelectedTabProvider>
                            <AppTabs />
                        </SelectedTabProvider>
                    </SnackbarProvider>
                </BrowserRouter>
            </QueryClientProvider>
        </ThemeProvider>
    );
}

export default App;
