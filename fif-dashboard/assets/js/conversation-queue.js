/* One ordered pipeline for selection greetings, remote requests and typing. */
(function () {
  const F = window.FIF;
  F.createConversationQueue = function (onChange = () => {}) {
    const jobs = [];
    let running = false;
    const report = () => onChange(jobs.length, running);
    async function drain() {
      if (running) return;
      running = true; report();
      while (jobs.length) {
        const job = jobs.shift(); report();
        try { job.resolve(await job.run()); } catch (error) { job.reject(error); }
      }
      running = false; report();
    }
    return {
      add(run) {
        const promise = new Promise((resolve, reject) => jobs.push({run, resolve, reject}));
        report(); drain(); return promise;
      },
      get pending() { return jobs.length; }
    };
  };
})();
