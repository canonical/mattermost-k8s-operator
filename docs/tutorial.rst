Deploy the Mattermost charm for the first time
===============================================

In this tutorial, we'll go through each step of the process to get a basic Mattermost deployment.

What you'll need
----------------

You will need a working station, e.g., a laptop, with AMD64 architecture. Your working station
should have at least 4 CPU cores, 8 GB of RAM, and 50 GB of disk space.

.. tip::

   You can use Multipass to create a virtual machine(VM) and work in an isolated environment by running:

   .. code-block:: bash

      multipass launch 24.04 --name mattermost-tutorial-vm --cpus 4 --memory 8G --disk 50G

Shell into the Multipass VM
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note::

   If you're working locally, you don't need to do this step.

To be able to work inside the Multipass VM first you need to log in with the following command:

.. code-block:: bash

   multipass shell mattermost-tutorial-vm

Install and prepare Juju and MicroK8s
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This tutorial requires the following software to be installed on your working station
(either locally or in the Multipass VM):

- Juju 3
- MicroK8s 1.35

Use `Concierge <https://github.com/canonical/concierge>`_ to set up Juju and MicroK8s:

.. code-block:: bash

   sudo snap install --classic concierge
   sudo concierge prepare -p microk8s

This first command installs Concierge, and the second command uses Concierge to install
and configure Juju and MicroK8s.

For this tutorial, Juju must be bootstrapped to a MicroK8s controller. Concierge should
complete this step for you, and you can verify by checking for ``msg="Bootstrapped Juju" provider=microk8s``
in the terminal output and by running ``juju controllers``.

If Concierge did not perform the bootstrap, run:

.. code-block:: bash

   juju bootstrap microk8s tutorial-controller

What you'll do
--------------

1. Deploy the Mattermost charm
2. Integrate with the PostgreSQL charm
3. Inspect the Kubernetes resources created
4. Access the Mattermost app and bootstrap
5. Clean up the environment

Add a Juju model for the tutorial
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To easily clean up the resources and separate your workload from the contents of this tutorial, set up a new Juju model named ``mattermost-tutorial``:

.. code-block:: bash

   juju add-model mattermost-tutorial

Deploy the charms
~~~~~~~~~~~~~~~~~

Mattermost requires connections to PostgreSQL. For more information, see the `Charm Integrations <https://charmhub.io/mattermost-k8s/docs/reference-integrations>`_.

Deploy the charms:

.. code-block:: bash

   juju deploy mattermost-k8s --channel latest/edge
   juju deploy postgresql-k8s --channel 14/stable --trust

The Mattermost database driver requires a secure SSL/TLS connection by default. For this tutorial, we will use the ``self-signed-certificates`` charm to provision a local Certificate Authority (CA) for PostgreSQL:

.. code-block:: bash

   juju deploy self-signed-certificates
   juju integrate postgresql-k8s self-signed-certificates:certificates

Integrate with the PostgreSQL charm
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Integrate ``postgresql-k8s`` to ``mattermost-k8s``:

.. code-block:: bash

   juju integrate mattermost-k8s postgresql-k8s

Inspect the status of the deployment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By running ``juju status --relations`` the current state of the deployment can be queried:

.. code-block:: text

   Model                Controller          Cloud/Region        Version  SLA          Timestamp
   mattermost-tutorial  concierge-microk8s  microk8s/localhost  3.6.21   unsupported  21:45:15+01:00

   App                       Version  Status  Scale  Charm                     Channel      Rev  Address         Exposed  Message
   mattermost-k8s                     active      1  mattermost-k8s            latest/edge   29  10.152.183.166  no
   postgresql-k8s            14.20    active      1  postgresql-k8s            14/stable    774  10.152.183.59   no
   self-signed-certificates           active      1  self-signed-certificates  1/stable     586  10.152.183.208  no

   Unit                         Workload  Agent  Address       Ports  Message
   mattermost-k8s/0*            active    idle   10.1.225.142
   postgresql-k8s/0*            active    idle   10.1.225.140         Primary
   self-signed-certificates/0*  active    idle   10.1.225.141

   Integration provider                   Requirer                       Interface          Type     Message
   mattermost-k8s:secret-storage          mattermost-k8s:secret-storage  secret-storage     peer
   postgresql-k8s:database                mattermost-k8s:postgresql      postgresql_client  regular
   postgresql-k8s:database-peers          postgresql-k8s:database-peers  postgresql_peers   peer
   postgresql-k8s:restart                 postgresql-k8s:restart         rolling_op         peer
   postgresql-k8s:upgrade                 postgresql-k8s:upgrade         upgrade            peer
   self-signed-certificates:certificates  postgresql-k8s:certificates    tls-certificates   regular

The deployment finishes when all the charms show ``Active`` states.

Run ``microk8s kubectl get pods -n mattermost-tutorial`` to see the pods that are being created by the charms:

.. code-block:: text

   NAME                            READY   STATUS    RESTARTS   AGE
   mattermost-k8s-0                2/2     Running   0          10m
   modeloperator-64cb49db9-8cvpv   1/1     Running   0          15m
   postgresql-k8s-0                2/2     Running   0          13m
   self-signed-certificates-0      1/1     Running   0          13m

.. note::

   If you are using ``multipass``, or installed ``microk8s`` from scratch, you might get an "insufficient permissions" error. In that case, run the commands presented at the error message in your terminal, after which you'll be able to run ``microk8s`` commands.

   .. code-block:: bash

      sudo usermod -a -G snap_microk8s ubuntu
      sudo chown -R ubuntu ~/.kube
      newgrp snap_microk8s

Access Mattermost for the first time
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default, ``mattermost`` is exposed on the port 8080. To find the internal IP address assigned to ``mattermost``, check the application address in the ``juju status`` output. For our example, this is ``10.152.183.239``. Open a web browser, navigate to ``10.152.183.239:8080`` and follow the steps to set up your Mattermost server.

.. note::

   If you are using ``multipass``, you need to forward the port to access the application from a web browser:

   .. code-block:: bash

      microk8s kubectl port-forward --address 0.0.0.0 service/mattermost-k8s 8080:8080 -n mattermost-tutorial

   Then, in a separate terminal in your host machine, you can find the address of your VM by running ``multipass info mattermost-tutorial-vm``.
   This would be the private IP address and usually would be listed first. Now, you can navigate to ``<your-multipass-vm-ip>:8080`` to access Mattermost.

Clean up the environment
~~~~~~~~~~~~~~~~~~~~~~~~~

Congratulations! You have successfully finished the Mattermost tutorial. You have now deployed the Mattermost charm, integrated it with a database, and accessed the Mattermost instance in your browser. You can now remove the
model environment that you've created using the following command:

.. code-block:: bash

   juju destroy-model mattermost-tutorial --destroy-storage

If you used Multipass, to remove the Multipass instance you created for this tutorial, use the following command on your host machine.

.. code-block:: bash

   multipass delete --purge mattermost-tutorial-vm
