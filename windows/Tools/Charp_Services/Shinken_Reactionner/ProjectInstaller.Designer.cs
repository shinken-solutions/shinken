namespace ShinkenReactionnerService
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
            this.ReactionnerProcessInstaller1 = new System.ServiceProcess.ServiceProcessInstaller();
            this.ReactionnerInstaller1 = new System.ServiceProcess.ServiceInstaller();
            // 
            // ReactionnerProcessInstaller1
            // 
            this.ReactionnerProcessInstaller1.Account = System.ServiceProcess.ServiceAccount.LocalSystem;
            this.ReactionnerProcessInstaller1.Installers.AddRange(new System.Configuration.Install.Installer[] {
            this.ReactionnerInstaller1});
            this.ReactionnerProcessInstaller1.Password = null;
            this.ReactionnerProcessInstaller1.Username = null;
            // 
            // ReactionnerInstaller1
            // 
            this.ReactionnerInstaller1.DisplayName = "Shinken Reactionner";
            this.ReactionnerInstaller1.ServiceName = "ShinkenReactionner_Service";
            this.ReactionnerInstaller1.StartType = System.ServiceProcess.ServiceStartMode.Automatic;
            // 
            // ProjectInstaller
            // 
            this.Installers.AddRange(new System.Configuration.Install.Installer[] {
            this.ReactionnerProcessInstaller1});

        }

        #endregion

        private System.ServiceProcess.ServiceProcessInstaller ReactionnerProcessInstaller1;
        private System.ServiceProcess.ServiceInstaller ReactionnerInstaller1;
    }
}