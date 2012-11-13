namespace ShinkenSchedulerService
{
    partial class ProjectInstaller
    {
        /// <summary>
        /// Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary> 
        /// Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Component Designer generated code

        /// <summary>
        /// Required method for Designer support - do not modify
        /// the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            this.SchedulerProcessInstaller1 = new System.ServiceProcess.ServiceProcessInstaller();
            this.SchedulerInstaller1 = new System.ServiceProcess.ServiceInstaller();
            // 
            // SchedulerProcessInstaller1
            // 
            this.SchedulerProcessInstaller1.Account = System.ServiceProcess.ServiceAccount.LocalSystem;
            this.SchedulerProcessInstaller1.Installers.AddRange(new System.Configuration.Install.Installer[] {
            this.SchedulerInstaller1});
            this.SchedulerProcessInstaller1.Password = null;
            this.SchedulerProcessInstaller1.Username = null;
            // 
            // SchedulerInstaller1
            // 
            this.SchedulerInstaller1.DisplayName = "Shinken Scheduler";
            this.SchedulerInstaller1.ServiceName = "ShinkenScheduler_Service";
            this.SchedulerInstaller1.StartType = System.ServiceProcess.ServiceStartMode.Automatic;
            // 
            // ProjectInstaller
            // 
            this.Installers.AddRange(new System.Configuration.Install.Installer[] {
            this.SchedulerProcessInstaller1});

        }

        #endregion

        private System.ServiceProcess.ServiceProcessInstaller SchedulerProcessInstaller1;
        private System.ServiceProcess.ServiceInstaller SchedulerInstaller1;
    }
}