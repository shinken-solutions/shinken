namespace ShinkenPollerService
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
            this.PollerProcessInstaller1 = new System.ServiceProcess.ServiceProcessInstaller();
            this.PollerInstaller1 = new System.ServiceProcess.ServiceInstaller();
            // 
            // PollerProcessInstaller1
            // 
            this.PollerProcessInstaller1.Account = System.ServiceProcess.ServiceAccount.LocalSystem;
            this.PollerProcessInstaller1.Installers.AddRange(new System.Configuration.Install.Installer[] {
            this.PollerInstaller1});
            this.PollerProcessInstaller1.Password = null;
            this.PollerProcessInstaller1.Username = null;
            // 
            // PollerInstaller1
            // 
            this.PollerInstaller1.DisplayName = "Shinken Poller";
            this.PollerInstaller1.ServiceName = "ShinkenPoller_Service";
            this.PollerInstaller1.StartType = System.ServiceProcess.ServiceStartMode.Automatic;
            // 
            // ProjectInstaller
            // 
            this.Installers.AddRange(new System.Configuration.Install.Installer[] {
            this.PollerProcessInstaller1});

        }

        #endregion

        private System.ServiceProcess.ServiceProcessInstaller PollerProcessInstaller1;
        private System.ServiceProcess.ServiceInstaller PollerInstaller1;
    }
}