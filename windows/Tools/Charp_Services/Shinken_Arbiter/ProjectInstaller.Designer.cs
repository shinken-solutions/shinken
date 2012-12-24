namespace ShinkenArbiterService
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
            this.ArbiterProcessInstaller1 = new System.ServiceProcess.ServiceProcessInstaller();
            this.ArbiterInstaller1 = new System.ServiceProcess.ServiceInstaller();
            // 
            // ArbiterProcessInstaller1
            // 
            this.ArbiterProcessInstaller1.Account = System.ServiceProcess.ServiceAccount.LocalSystem;
            this.ArbiterProcessInstaller1.Installers.AddRange(new System.Configuration.Install.Installer[] {
            this.ArbiterInstaller1});
            this.ArbiterProcessInstaller1.Password = null;
            this.ArbiterProcessInstaller1.Username = null;
            // 
            // ArbiterInstaller1
            // 
            this.ArbiterInstaller1.DisplayName = "Shinken Arbiter";
            this.ArbiterInstaller1.ServiceName = "ShinkenArbiter_Service";
            this.ArbiterInstaller1.StartType = System.ServiceProcess.ServiceStartMode.Automatic;
            // 
            // ProjectInstaller
            // 
            this.Installers.AddRange(new System.Configuration.Install.Installer[] {
            this.ArbiterProcessInstaller1});

        }

        #endregion

        private System.ServiceProcess.ServiceProcessInstaller ArbiterProcessInstaller1;
        private System.ServiceProcess.ServiceInstaller ArbiterInstaller1;
    }
}