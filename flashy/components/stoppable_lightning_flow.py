from lightning import LightningFlow


class StoppableLightningFlow(LightningFlow):
    def stop(self):
        """Stop all works owned by this ``DashboardManager`` and clear the layout."""
        for work_name, work in self.named_works():
            # TODO: Add a method in the base ``LightningFlow`` to stop and remove a work
            work.stop()
            delattr(self, work_name)
            self._works.remove(work_name)
