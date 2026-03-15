class SurfaceAdapter:
    def publish(self, profile, state, plan, results, verification, replay_events):
        raise NotImplementedError

    def publish_abort(self, profile, state, plan, replay_events):
        raise NotImplementedError
