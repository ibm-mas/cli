IBM Maximo Operator Catalog
-------------------------------------------------------------------------------
This catalog is a **curated** catalog, the Maximo Application Suite team take a snapshot of the online IBM Operator Catalog and test compatibility of all dependent IBM operators with supported releases of Maximo Application Suite; this allows the team to intercept any breaking changes that may have evaded other teams' testing before they reach your cluster.

### Availability
All versions of the catalog are available **indefinitely**, but they have a useful lifespan limited by the support statements of the packages available in the catalog and the OCP release the catalog is certified on.  We **never** remove catalog images from the IBM Container Registry (ICR); even the [first](v8-220717-amd64.md) Maximo Operator Catalog ever published is still available today, however it's usefulness is questionable due to the end of life of all compatible OCP releases.

### CLI Support
The MAS CLI maintains a rolling window of approximately four months worth of supported catalogs for the install, mirror-images, and update functions.  When using an older catalog it is recommended to use a version of the CLI that was released around the same time as the catalog, refer to the table below for the recommended version of the CLI to use with older versions of the operator catalog.


### Catalog Directory
Note: The Red Hat Extended Update Support Add-on Term 1 offering is included with the OCP subscription that comes with a MAS license. In the case of EUS denoted OCP releases, the support dates stated below refer to the EUS1 end dates.  For more details on the OCP support lifecycle see: [https://access.redhat.com/support/policy/updates/openshift](https://access.redhat.com/support/policy/updates/openshift).  Also note that support for the non-EUS releases expires before the extended support for the previous EUS release, for example extended support for OCP 4.18 expires on Feb 25, 2027, while standard support for OCP 4.17 expires on April 1, 2026.
Note: The Red Hat Extended Update Support Add-on Term 1 offering is included with the OCP subscription that comes with a MAS license. In the case of EUS denoted OCP releases, the support dates stated below refer to the EUS1 end dates.  For more details on the OCP support lifecycle see: [https://access.redhat.com/support/policy/updates/openshift](https://access.redhat.com/support/policy/updates/openshift).  Also note that support for the non-EUS releases expires before the extended support for the previous EUS release, for example extended support for OCP 4.18 expires on Feb 25, 2027, while standard support for OCP 4.17 expires on April 1, 2026.

<cds-tabs trigger-content="Select an item" value="2026">
<cds-tabs trigger-content="Select an item" value="2026">
  <cds-tab id="tab-2026" target="panel-2026" value="2026">2026 Catalogs</cds-tab>
  <cds-tab id="tab-2025" target="panel-2025" value="2025">2025 Catalogs</cds-tab>
  <cds-tab id="tab-2024" target="panel-2024" value="2024">2024 Catalogs</cds-tab>
  <cds-tab id="tab-2023" target="panel-2023" value="2023">2023 Catalogs</cds-tab>
  <cds-tab id="tab-2022" target="panel-2022" value="2022">2022 Catalogs</cds-tab>
</cds-tabs>

<div class="tab-panel">
  <div id="panel-2026" role="tabpanel" aria-labelledby="tab-2026" hidden>
    <table>
      <thead>
        <tr>
          <th style="min-width: 200px;">Catalog</th>
          <th>OCP</th>
          <th>CPD</th>
          <th>MongoDB</th>
          <th>CLI</th>
          <th style="min-width: 200px;">Catalog</th>
          <th>OCP</th>
          <th>CPD</th>
          <th>MongoDB</th>
          <th>CLI</th>
        </tr>
      </thead>
      <tbody>
      <tr>
          <td style="font-style: italic">v9-261224<br/>amd64 | s390x | ppc64le</td>
          <td style="font-style: italic">TBD<br/></td>
          <td style="font-style: italic">TBD</td>
          <td style="font-style: italic">TBD</td>
          <td style="font-style: italic">N/A</td>
        </tr>
      <tr>
          <td style="font-style: italic">v9-261126<br/>amd64 | s390x | ppc64le</td>
          <td style="font-style: italic">TBD<br/></td>
          <td style="font-style: italic">TBD</td>
          <td style="font-style: italic">TBD</td>
          <td style="font-style: italic">N/A</td>
        </tr>
        <tr>
          <td style="font-style: italic">v9-261029<br/>amd64 | s390x | ppc64le</td>
          <td style="font-style: italic">TBD<br/></td>
          <td style="font-style: italic">TBD</td>
          <td style="font-style: italic">TBD</td>
          <td style="font-style: italic">N/A</td>
        </tr>
        <tr>
          <td style="font-style: italic">v9-260924<br/>amd64 | s390x | ppc64le</td>
          <td style="font-style: italic">TBD<br/></td>
          <td style="font-style: italic">TBD</td>
          <td style="font-style: italic">TBD</td>
          <td style="font-style: italic">N/A</td>
        </tr>
        <tr>
          <td style="font-style: italic">v9-260827<br/>amd64 | s390x | ppc64le</td>
          <td style="font-style: italic">TBD<br/></td>
          <td style="font-style: italic">TBD</td>
          <td style="font-style: italic">TBD</td>
          <td style="font-style: italic">N/A</td>
        </tr>
        <tr>
          <td style="font-style: italic">v9-260730<br/>amd64 | s390x | ppc64le</td>
          <td style="font-style: italic">TBD<br/></td>
          <td style="font-style: italic">TBD</td>
          <td style="font-style: italic">TBD</td>
          <td style="font-style: italic">N/A</td>
        </tr>
        <tr>
          <td style="font-style: italic">v9-260625<br/>amd64 | s390x | ppc64le</td>
          <td style="font-style: italic">TBD<br/></td>
          <td style="font-style: italic">TBD</td>
          <td style="font-style: italic">TBD</td>
          <td style="font-style: italic">N/A</td>
        </tr>
        <tr>
          <td style="font-style: italic">v9-260528<br/>amd64 | s390x | ppc64le</td>
          <td style="font-style: italic">TBD<br/></td>
          <td style="font-style: italic">TBD</td>
          <td style="font-style: italic">TBD</td>
          <td style="font-style: italic">N/A</td>
        </tr>
        <tr>
          <td style="font-style: italic">v9-260423<br/>amd64 | s390x | ppc64le</td>
          <td style="font-style: italic">TBD<br/></td>
          <td style="font-style: italic">TBD</td>
          <td style="font-style: italic">TBD</td>
          <td style="font-style: italic">N/A</td>
        </tr>
        <tr>
          <td style="font-style: italic">v9-260326<br/>amd64 | s390x | ppc64le</td>
          <td style="font-style: italic">TBD<br/></td>
          <td style="font-style: italic">TBD</td>
          <td style="font-style: italic">TBD</td>
          <td style="font-style: italic">N/A</td>
        </tr>
        <tr>
          <td style="font-style: italic">v9-260226<br/>amd64 | s390x | ppc64le</td>
          <td style="font-style: italic">TBD<br/></td>
          <td style="font-style: italic">TBD</td>
          <td style="font-style: italic">TBD</td>
          <td style="font-style: italic">N/A</td>
        </tr>
        <tr>
          <td><span style="font-weight: bold">v9-260129</span><br/><a href="v9-260129-amd64/">amd64</a> | <a href="v9-260129-s390x/">s390x</a> | <a href="v9-260129-ppc64le/">ppc64le</a></td>
          <td><span style="font-weight: bold">4.16 - 4.19</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Feb 25, 2027 ↗</a></td>
          <td><span style="font-weight: bold">v9-260129</span><br/><a href="v9-260129-amd64/">amd64</a> | <a href="v9-260129-s390x/">s390x</a> | <a href="v9-260129-ppc64le/">ppc64le</a></td>
          <td><span style="font-weight: bold">4.16 - 4.19</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Feb 25, 2027 ↗</a></td>
          <td>5.2.0</td>
          <td>7.0 - 8.0</td>
          <td>latest</td>
        </tr>
        </tbody>
    </table>
  </div>

  <div id="panel-2025" role="tabpanel" aria-labelledby="tab-2025" hidden>
    <table>
      <thead>
        <tr>
          <th style="min-width: 200px;">Catalog</th>
          <th>OCP</th>
          <th>CPD</th>
          <th>MongoDB</th>
          <th>CLI</th>
          <th style="min-width: 200px;">Catalog</th>
          <th>OCP</th>
          <th>CPD</th>
          <th>MongoDB</th>
          <th>CLI</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><span style="font-weight: bold">v9-251231</span><br/><a href="v9-251231-amd64/">amd64</a> | <a href="v9-251231-s390x/">s390x</a> | <a href="v9-251231-ppc64le/">ppc64le</a></td>
          <td><span style="font-weight: bold">4.16 - 4.19</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Feb 25, 2027 ↗</a></td>
          <td><span style="font-weight: bold">v9-251231</span><br/><a href="v9-251231-amd64/">amd64</a> | <a href="v9-251231-s390x/">s390x</a> | <a href="v9-251231-ppc64le/">ppc64le</a></td>
          <td><span style="font-weight: bold">4.16 - 4.19</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Feb 25, 2027 ↗</a></td>
          <td>5.2.0</td>
          <td>7.0 - 8.0</td>
          <td>latest</td>
        </tr>
        <tr>
          <td><span style="font-weight: bold">v9-251224</span><br/><a href="v9-251224-amd64/">amd64</a> | <a href="v9-251224-s390x/">s390x</a> | <a href="v9-251224-ppc64le/">ppc64le</a></td>
          <td><span style="font-weight: bold">4.16 - 4.19</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Feb 25, 2027 ↗</a></td>
          <td><span style="font-weight: bold">v9-251224</span><br/><a href="v9-251224-amd64/">amd64</a> | <a href="v9-251224-s390x/">s390x</a> | <a href="v9-251224-ppc64le/">ppc64le</a></td>
          <td><span style="font-weight: bold">4.16 - 4.19</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Feb 25, 2027 ↗</a></td>
          <td>5.2.0</td>
          <td>7.0 - 8.0</td>
          <td>latest</td>
          <td>latest</td>
        </tr>
        <tr>
          <td><span style="font-weight: bold">v9-251127</span><br/><a href="v9-251127-amd64/">amd64</a> | <a href="v9-251127-s390x/">s390x</a> | <a href="v9-251127-ppc64le/">ppc64le</a></td>
          <td><span style="font-weight: bold">4.16 - 4.19</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Feb 25, 2027 ↗</a></td>
          <td><span style="font-weight: bold">v9-251127</span><br/><a href="v9-251127-amd64/">amd64</a> | <a href="v9-251127-s390x/">s390x</a> | <a href="v9-251127-ppc64le/">ppc64le</a></td>
          <td><span style="font-weight: bold">4.16 - 4.19</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Feb 25, 2027 ↗</a></td>
          <td>5.1.3</td>
          <td>7.0 - 8.0</td>
          <td>latest</td>
        </tr>
        <tr>
          <td><span style="font-weight: bold">v9-251030</span><br/><a href="v9-251030-amd64/">amd64</a> | <a href="v9-251030-s390x/">s390x</a> | <a href="v9-251030-ppc64le/">ppc64le</a></td>
          <td><span style="font-weight: bold">4.14 - 4.19</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Feb 25, 2027 ↗</a></td>
          <td><span style="font-weight: bold">v9-251030</span><br/><a href="v9-251030-amd64/">amd64</a> | <a href="v9-251030-s390x/">s390x</a> | <a href="v9-251030-ppc64le/">ppc64le</a></td>
          <td><span style="font-weight: bold">4.14 - 4.19</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Feb 25, 2027 ↗</a></td>
          <td>5.1.3</td>
          <td>6.0 - 7.0</td>
          <td>15.11.0</td>
        </tr>
        <tr>
          <td><span style="font-weight: bold">v9-251010</span><br/><a href="v9-251010-amd64/">amd64</a> | <a href="v9-251010-ppc64le/">ppc64le</a></td>
          <td><span style="font-weight: bold">4.14 - 4.18</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Feb 25, 2027 ↗</a></td>
          <td><span style="font-weight: bold">v9-251010</span><br/><a href="v9-251010-amd64/">amd64</a> | <a href="v9-251010-ppc64le/">ppc64le</a></td>
          <td><span style="font-weight: bold">4.14 - 4.18</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Feb 25, 2027 ↗</a></td>
          <td>5.1.3</td>
          <td>6.0 - 7.0</td>
          <td>15.9.0</td>
        </tr>
        <tr>
          <td><span style="font-weight: bold">v9-250925</span><br/><a href="v9-250925-amd64/">amd64</a> | <a href="v9-250925-ppc64le/">ppc64le</a></td>
          <td><span style="font-weight: bold">4.14 - 4.18</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Feb 25, 2027 ↗</a></td>
          <td><span style="font-weight: bold">v9-250925</span><br/><a href="v9-250925-amd64/">amd64</a> | <a href="v9-250925-ppc64le/">ppc64le</a></td>
          <td><span style="font-weight: bold">4.14 - 4.18</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Feb 25, 2027 ↗</a></td>
          <td>5.1.3</td>
          <td>6.0 - 7.0</td>
          <td>15.7.0</td>
        </tr>
        <tr>
          <td><span style="font-weight: bold">v9-250902</span><br/><a href="v9-250902-amd64/">amd64</a> | <a href="v9-250902-s390x/">s390x</a> | <a href="v9-250902-ppc64le/">ppc64le</a></td>
          <td><span style="font-weight: bold">4.14 - 4.18</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Feb 25, 2027 ↗</a></td>
          <td><span style="font-weight: bold">v9-250902</span><br/><a href="v9-250902-amd64/">amd64</a> | <a href="v9-250902-s390x/">s390x</a> | <a href="v9-250902-ppc64le/">ppc64le</a></td>
          <td><span style="font-weight: bold">4.14 - 4.18</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Feb 25, 2027 ↗</a></td>
          <td>5.1.3</td>
          <td>6.0 - 7.0</td>
          <td>15.3.0</td>
        </tr>
        <tr>
          <td><span style="font-weight: bold">v9-250828</span><br/><a href="v9-250828-amd64/">amd64</a> | <a href="v9-250828-s390x/">s390x</a> | <a href="v9-250828-ppc64le/">ppc64le</a></td>
          <td><span style="font-weight: bold">4.14 - 4.18</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Feb 25, 2027 ↗</a></td>
          <td><span style="font-weight: bold">v9-250828</span><br/><a href="v9-250828-amd64/">amd64</a> | <a href="v9-250828-s390x/">s390x</a> | <a href="v9-250828-ppc64le/">ppc64le</a></td>
          <td><span style="font-weight: bold">4.14 - 4.18</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Feb 25, 2027 ↗</a></td>
          <td>5.1.3</td>
          <td>6.0 - 7.0</td>
          <td>15.2.0</td>
        </tr>
        <tr>
          <td><span style="font-weight: bold">v9-250731</span><br/><a href="v9-250731-amd64/">amd64</a> | <a href="v9-250731-s390x/">s390x</a> | <a href="v9-250731-ppc64le/">ppc64le</a></td>
          <td><span style="font-weight: bold">4.14 - 4.18</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Feb 25, 2027 ↗</a></td>
          <td><span style="font-weight: bold">v9-250731</span><br/><a href="v9-250731-amd64/">amd64</a> | <a href="v9-250731-s390x/">s390x</a> | <a href="v9-250731-ppc64le/">ppc64le</a></td>
          <td><span style="font-weight: bold">4.14 - 4.18</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Feb 25, 2027 ↗</a></td>
          <td>5.1.3</td>
          <td>6.0 - 7.0</td>
          <td>15.1.0</td>
        </tr>
        <tr>
          <td><span style="font-weight: bold">v9-250624</span><br/><a href="v9-250624-amd64/">amd64</a> | <a href="v9-250624-s390x/">s390x</a> | <a href="v9-250624-ppc64le/">ppc64le</a></td>
          <td><span style="font-weight: bold">4.14 - 4.18</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Feb 25, 2027 ↗</a></td>
          <td><span style="font-weight: bold">v9-250624</span><br/><a href="v9-250624-amd64/">amd64</a> | <a href="v9-250624-s390x/">s390x</a> | <a href="v9-250624-ppc64le/">ppc64le</a></td>
          <td><span style="font-weight: bold">4.14 - 4.18</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Feb 25, 2027 ↗</a></td>
          <td>5.1.3</td>
          <td>6.0 - 7.0</td>
          <td>13.26.0</td>
        </tr>
        <tr>
          <td><span style="font-weight: bold">v9-250501</span><br/><a href="v9-250501-amd64/">amd64</a> | <a href="v9-250501-s390x/">s390x</a> | N/A</td>
          <td><span style="font-weight: bold">4.14 - 4.16</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Jun 27, 2026 ↗</a></td>
          <td><span style="font-weight: bold">v9-250501</span><br/><a href="v9-250501-amd64/">amd64</a> | <a href="v9-250501-s390x/">s390x</a> | N/A</td>
          <td><span style="font-weight: bold">4.14 - 4.16</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Jun 27, 2026 ↗</a></td>
          <td>5.0.0</td>
          <td>6.0 - 7.0</td>
          <td>13.20.0</td>
        </tr>
        <tr>
          <td><span style="font-weight: bold">v9-250403</span><br/><a href="v9-250403-amd64/">amd64</a> | <a href="v9-250403-s390x/">s390x</a> | N/A</td>
          <td><span style="font-weight: bold">4.14 - 4.16</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Jun 27, 2026 ↗</a></td>
          <td><span style="font-weight: bold">v9-250403</span><br/><a href="v9-250403-amd64/">amd64</a> | <a href="v9-250403-s390x/">s390x</a> | N/A</td>
          <td><span style="font-weight: bold">4.14 - 4.16</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Jun 27, 2026 ↗</a></td>
          <td>5.0.0</td>
          <td>6.0 - 7.0</td>
          <td>13.15.0</td>
        </tr>
        <tr>
          <td><span style="font-weight: bold">v9-250306</span><br/><a href="v9-250306-amd64/">amd64</a> | <a href="v9-250306-s390x/">s390x</a> | N/A</td>
          <td><span style="font-weight: bold">4.14 - 4.16</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Jun 27, 2026 ↗</a></td>
          <td><span style="font-weight: bold">v9-250306</span><br/><a href="v9-250306-amd64/">amd64</a> | <a href="v9-250306-s390x/">s390x</a> | N/A</td>
          <td><span style="font-weight: bold">4.14 - 4.16</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Jun 27, 2026 ↗</a></td>
          <td>5.0.0</td>
          <td>6.0 - 7.0</td>
          <td>13.10.0</td>
        </tr>
        <tr>
          <td><span style="font-weight: bold">v9-250206</span><br/><a href="v9-250206-amd64/">amd64</a> | <a href="v9-250206-s390x/">s390x</a> | N/A</td>
          <td><span style="font-weight: bold">4.14 - 4.16</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Jun 27, 2026 ↗</a></td>
          <td><span style="font-weight: bold">v9-250206</span><br/><a href="v9-250206-amd64/">amd64</a> | <a href="v9-250206-s390x/">s390x</a> | N/A</td>
          <td><span style="font-weight: bold">4.14 - 4.16</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Jun 27, 2026 ↗</a></td>
          <td>5.0.0</td>
          <td>6.0 - 7.0</td>
          <td>13.3.0</td>
        </tr>
        <tr>
          <td><span style="font-weight: bold">v9-250109</span><br/><a href="v9-250109-amd64/">amd64</a> | <a href="v9-250109-s390x/">s390x</a> | N/A</td>
          <td><span style="font-weight: bold">4.14 - 4.16</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Jun 27, 2026 ↗</a></td>
          <td><span style="font-weight: bold">v9-250109</span><br/><a href="v9-250109-amd64/">amd64</a> | <a href="v9-250109-s390x/">s390x</a> | N/A</td>
          <td><span style="font-weight: bold">4.14 - 4.16</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Jun 27, 2026 ↗</a></td>
          <td>5.0.0</td>
          <td>6.0 - 7.0</td>
          <td>13.0.0</td>
        </tr>
      </tbody>
    </table>
  </div>
  <div id="panel-2024" role="tabpanel" aria-labelledby="tab-2024" hidden>
    <table>
    <thead>
    <tr>
    <th>Catalog</th>
    <th>OCP</th>
    <th>CPD</th>
    <th>MongoDB</th>
    <th>CLI</th>
    <th>OCP</th>
    <th>CPD</th>
    <th>MongoDB</th>
    <th>CLI</th>
    </tr>
    </thead>
    <tbody>
    <tr>
    <td><span style="font-weight: bold">v9-241205</span><br/><a href="v9-241205-amd64/">amd64</a> | <a href="v9-241205-s390x/">s390x</a></td>
    <td><span style="font-weight: bold">4.14 - 4.16</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Jun 27, 2026 ↗</a></td>
    <td><span style="font-weight: bold">v9-241205</span><br/><a href="v9-241205-amd64/">amd64</a> | <a href="v9-241205-s390x/">s390x</a></td>
    <td><span style="font-weight: bold">4.14 - 4.16</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Jun 27, 2026 ↗</a></td>
    <td>5.0.0</td>
    <td>6.0 - 7.0</td>
    <td>11.12.0</td>
    </tr>
    <tr>
    <td><span style="font-weight: bold">v9-241107</span><br/><a href="v9-241107-amd64/">amd64</a> | <a href="v9-241107-s390x/">s390x</a></td>
    <td><span style="font-weight: bold">4.12 - 4.15</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Aug 27, 2025 ↗</a></td>
    <td><span style="font-weight: bold">v9-241107</span><br/><a href="v9-241107-amd64/">amd64</a> | <a href="v9-241107-s390x/">s390x</a></td>
    <td><span style="font-weight: bold">4.12 - 4.15</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Aug 27, 2025 ↗</a></td>
    <td>4.8.0</td>
    <td>6.0 - 7.0</td>
    <td>11.7.0</td>
    </tr>
    <tr>
    <td><a href="v9-241003-amd64/"><span style="font-weight: bold">v9-241003-amd64</span></a></td>
    <td><span style="font-weight: bold">4.12 - 4.15</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Aug 27, 2025 ↗</a></td>
    <td><a href="v9-241003-amd64/"><span style="font-weight: bold">v9-241003-amd64</span></a></td>
    <td><span style="font-weight: bold">4.12 - 4.15</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Aug 27, 2025 ↗</a></td>
    <td>4.8.0</td>
    <td>5.0 - 7.0</td>
    <td>13.0.0</td>
    </tr>
    <tr>
    <td><a href="v9-240827-amd64/"><span style="font-weight: bold">v9-240827-amd64</span></a></td>
    <td><span style="font-weight: bold">4.12 - 4.15</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Aug 27, 2025 ↗</a></td>
    <td><a href="v9-240827-amd64/"><span style="font-weight: bold">v9-240827-amd64</span></a></td>
    <td><span style="font-weight: bold">4.12 - 4.15</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Aug 27, 2025 ↗</a></td>
    <td>4.8.0</td>
    <td>5.0 - 7.0</td>
    <td>11.11.3</td>
    </tr>
    <tr>
    <td><a href="v9-240730-amd64/"><span style="font-weight: bold">v9-240730-amd64</span></a></td>
    <td><span style="font-weight: bold">4.12 - 4.15</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Aug 27, 2025 ↗</a></td>
    <td><a href="v9-240730-amd64/"><span style="font-weight: bold">v9-240730-amd64</span></a></td>
    <td><span style="font-weight: bold">4.12 - 4.15</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Aug 27, 2025 ↗</a></td>
    <td>4.8.0</td>
    <td>5.0 - 7.0</td>
    <td>11.5.0</td>
    </tr>
    <tr>
    <td><a href="v9-240625-amd64/"><span style="font-weight: bold">v9-240625-amd64</span></a></td>
    <td><span style="font-weight: bold">4.12 - 4.14</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Oct 31, 2025 ↗</a></td>
    <td><a href="v9-240625-amd64/"><span style="font-weight: bold">v9-240625-amd64</span></a></td>
    <td><span style="font-weight: bold">4.12 - 4.14</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Oct 31, 2025 ↗</a></td>
    <td>4.8.0</td>
    <td>5.0 - 7.0</td>
    <td>10.9.2</td>
    </tr>
    <tr>
    <td><a href="v8-240528-amd64/"><span style="font-weight: bold">v8-240528-amd64</span></a></td>
    <td><span style="font-weight: bold">4.12 - 4.14</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Oct 31, 2025 ↗</a></td>
    <td><a href="v8-240528-amd64/"><span style="font-weight: bold">v8-240528-amd64</span></a></td>
    <td><span style="font-weight: bold">4.12 - 4.14</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Oct 31, 2025 ↗</a></td>
    <td>4.6.6</td>
    <td>5.0 - 7.0</td>
    <td>10.8.1</td>
    </tr>
    <tr>
    <td><a href="v8-240430-amd64/"><span style="font-weight: bold">v8-240430-amd64</span></a></td>
    <td><span style="font-weight: bold">4.12 - 4.14</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Oct 31, 2025 ↗</a></td>
    <td><a href="v8-240430-amd64/"><span style="font-weight: bold">v8-240430-amd64</span></a></td>
    <td><span style="font-weight: bold">4.12 - 4.14</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Oct 31, 2025 ↗</a></td>
    <td>4.6.6</td>
    <td>5.0 - 7.0</td>
    <td>9.4.0</td>
    </tr>
    <tr>
    <td><a href="v8-240405-amd64/"><span style="font-weight: bold">v8-240405-amd64</span></a></td>
    <td><span style="font-weight: bold">4.12 - 4.14</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Oct 31, 2025 ↗</a></td>
    <td><a href="v8-240405-amd64/"><span style="font-weight: bold">v8-240405-amd64</span></a></td>
    <td><span style="font-weight: bold">4.12 - 4.14</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Oct 31, 2025 ↗</a></td>
    <td>4.6.6</td>
    <td>5.0 - 7.0</td>
    <td>9.4.0</td>
    </tr>
    <tr>
    <td><a href="v8-240326-amd64/"><span style="font-weight: bold">v8-240326-amd64</span></a></td>
    <td><span style="font-weight: bold">4.12 - 4.14</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Oct 31, 2025 ↗</a></td>
    <td><a href="v8-240326-amd64/"><span style="font-weight: bold">v8-240326-amd64</span></a></td>
    <td><span style="font-weight: bold">4.12 - 4.14</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Oct 31, 2025 ↗</a></td>
    <td>4.6.6</td>
    <td>5.0 - 7.0</td>
    <td>9.4.0</td>
    </tr>
    <tr>
    <td><a href="v8-240227-amd64/"><span style="font-weight: bold">v8-240227-amd64</span></a></td>
    <td><span style="font-weight: bold">4.12</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Jan 17, 2025 ↗</a></td>
    <td><a href="v8-240227-amd64/"><span style="font-weight: bold">v8-240227-amd64</span></a></td>
    <td><span style="font-weight: bold">4.12</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Jan 17, 2025 ↗</a></td>
    <td>4.6.6</td>
    <td>5.0 - 7.0</td>
    <td>8.2.2</td>
    </tr>
    <tr>
    <td><a href="v8-240130-amd64/"><span style="font-weight: bold">v8-240130-amd64</span></a></td>
    <td><span style="font-weight: bold">4.12</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Jan 17, 2025 ↗</a></td>
    <td><a href="v8-240130-amd64/"><span style="font-weight: bold">v8-240130-amd64</span></a></td>
    <td><span style="font-weight: bold">4.12</span><br/><a href="https://access.redhat.com/support/policy/updates/openshift" target="_blank">EOS Jan 17, 2025 ↗</a></td>
    <td>4.6.6</td>
    <td>5.0 - 7.0</td>
    <td>8.2.2</td>
    </tr>
    </tbody>
    </table>
  </div>
  <div id="panel-2023" role="tabpanel" aria-labelledby="tab-2023" hidden>
    <table>
    <thead>
    <tr>
    <th>Catalog</th>
    <th>OCP</th>
    <th>CLI</th>
    <th>OCP</th>
    <th>CLI</th>
    <th>Support Notes</th>
    </tr>
    </thead>
    <tbody>
    <tr>
    <td><a href="v8-231228-amd64/">v8-231228-amd64</a></td>
    <td>4.11 - 4.12</td>
    <td>8.2.2</td>
    <td>OCP 4.12 EOS January 17, 2025</td>
    </tr>
    <tr>
    <td><a href="v8-231128-amd64/">v8-231128-amd64</a></td>
    <td>4.11 - 4.12</td>
    <td>8.2.2</td>
    <td>OCP 4.12 EOS January 17, 2025</td>
    </tr>
    <tr>
    <td><a href="v8-231031-amd64/">v8-231031-amd64</a></td>
    <td>4.11 - 4.12</td>
    <td>7.12.1</td>
    <td>OCP 4.12 EOS January 17, 2025</td>
    </tr>
    <tr>
    <td><a href="v8-231004-amd64/">v8-231004-amd64</a></td>
    <td>4.11 - 4.12</td>
    <td>7.12.1</td>
    <td>OCP 4.12 EOS January 17, 2025</td>
    </tr>
    <tr>
    <td><a href="v8-230926-amd64/">v8-230926-amd64</a></td>
    <td>4.11 - 4.12</td>
    <td>7.12.1</td>
    <td>OCP 4.12 EOS January 17, 2025</td>
    </tr>
    <tr>
    <td><a href="v8-230829-amd64/">v8-230829-amd64</a></td>
    <td>4.10 - 4.12</td>
    <td>7.12.1</td>
    <td>OCP 4.12 EOS January 17, 2025</td>
    </tr>
    <tr>
    <td><a href="v8-230725-amd64/">v8-230725-amd64</a></td>
    <td>4.10 - 4.12</td>
    <td>7.12.1</td>
    <td>OCP 4.12 EOS January 17, 2025</td>
    </tr>
    <tr>
    <td><a href="v8-230721-amd64/">v8-230721-amd64</a></td>
    <td>4.10 - 4.12</td>
    <td>7.12.1</td>
    <td>OCP 4.12 EOS January 17, 2025</td>
    </tr>
    <tr>
    <td><a href="v8-230627-amd64/">v8-230627-amd64</a></td>
    <td>4.10 - 4.12</td>
    <td>5.5.0</td>
    <td>OCP 4.12 EOS January 17, 2025</td>
    </tr>
    <tr>
    <td><a href="v8-230616-amd64/">v8-230616-amd64</a></td>
    <td>4.10 - 4.12</td>
    <td>5.5.0</td>
    <td>OCP 4.12 EOS January 17, 2025</td>
    </tr>
    <tr>
    <td><a href="v8-230526-amd64/">v8-230526-amd64</a></td>
    <td>4.10</td>
    <td>5.5.0</td>
    <td>OCP 4.10 EOS September 10, 2023</td>
    </tr>
    <tr>
    <td><a href="v8-230518-amd64/">v8-230518-amd64</a></td>
    <td>4.10</td>
    <td>5.5.0</td>
    <td>OCP 4.10 EOS September 10, 2023</td>
    </tr>
    <tr>
    <td><a href="v8-230414-amd64/">v8-230414-amd64</a></td>
    <td>4.8 - 4.10</td>
    <td>5.5.0</td>
    <td>OCP 4.10 EOS September 10, 2023</td>
    </tr>
    <tr>
    <td><a href="v8-230314-amd64/">v8-230314-amd64</a></td>
    <td>4.8 - 4.10</td>
    <td>4.3.1</td>
    <td>OCP 4.10 EOS September 10, 2023</td>
    </tr>
    <tr>
    <td><a href="v8-230217-amd64/">v8-230217-amd64</a></td>
    <td>4.8 - 4.10</td>
    <td>4.3.1</td>
    <td>OCP 4.10 EOS September 10, 2023</td>
    </tr>
    <tr>
    <td><a href="v8-230111-amd64/">v8-230111-amd64</a></td>
    <td>4.8 - 4.10</td>
    <td>4.3.1</td>
    <td>OCP 4.10 EOS September 10, 2023</td>
    </tr>
    </tbody>
    </table>
  </div>
  <div id="panel-2022" role="tabpanel" aria-labelledby="tab-2022" hidden>
    <table>
    <thead>
    <tr>
    <th>Catalog</th>
    <th>OCP</th>
    <th>CLI</th>
    <th>OCP</th>
    <th>CLI</th>
    <th>Support Notes</th>
    </tr>
    </thead>
    <tbody>
    <tr>
    <td><a href="v8-221228-amd64/">v8-221228-amd64</a></td>
    <td>4.6 - 4.10</td>
    <td>3.9.0</td>
    <td>OCP 4.10 EOS September 10, 2023</td>
    </tr>
    <tr>
    <td><a href="v8-221129-amd64/">v8-221129-amd64</a></td>
    <td>4.6 - 4.10</td>
    <td>3.9.0</td>
    <td>OCP 4.10 EOS September 10, 2023</td>
    </tr>
    <tr>
    <td><a href="v8-221025-amd64/">v8-221025-amd64</a></td>
    <td>4.6 - 4.10</td>
    <td>3.9.0</td>
    <td>OCP 4.10 EOS September 10, 2023</td>
    </tr>
    <tr>
    <td><a href="v8-220927-amd64/">v8-220927-amd64</a></td>
    <td>4.6 - 4.10</td>
    <td>3.5.0</td>
    <td>OCP 4.10 EOS September 10, 2023</td>
    </tr>
    <tr>
    <td><a href="v8-220805-amd64/">v8-220805-amd64</a></td>
    <td>4.6 - 4.10</td>
    <td>3.5.0</td>
    <td>OCP 4.10 EOS September 10, 2023</td>
    </tr>
    <tr>
    <td><a href="v8-220717-amd64/">v8-220717-amd64</a></td>
    <td>4.6 - 4.10</td>
    <td>3.5.0</td>
    <td>OCP 4.10 EOS September 10, 2023</td>
    </tr>
    </tbody>
    </table>
  </div>
</div>


### FAQ
#### User-Controlled Updates
> I want to control when updates are introduced into my cluster

The packages available in the Maximo Operator Catalog are fixed. Multiple installations at different times will always result in exactly the same version of all IBM-provided operators being installed.  To receive security updates and bug fixes you must periodically update the version of the static catalog that you have installed in the cluster.  Once you do this all operators that you have installed from the catalog will automatically update to the newer version.  We aim to release a catalog update monthly.  When you are ready to apply updates you simply modify the CatalogSource installed in your cluster, changing it from e.g. `@@MAS_PREVIOUS_CATALOG@@` to `@@MAS_LATEST_CATALOG@@`.

We **strongly discourage the use of manual update approval strategy for operator subscriptions** and all IBM-provided automation is designed to work with the automatic update approval strategy only.  In our experience the use of manual subscription approvals leads to overly complicated updates requiring significant administrative effort when taking into account the range of operators running in a cluster across numerous namespaces. We promote a model of **controling when updates are introduced to a cluster at the catalog level**.

Updating the operators is only one aspect of keeping a system up to date, when using the MAS CLI [update](../guides/update.md) function many other additional actions will be performed autoamtically, if you are not using the MAS CLI to drive updates then you should implement your own processes for the non-operator update actions that are part of the MAS update pipeline.

#### Repeatable Install
> I want repeatable installs across multiple OpenShift clusters, for instance in a development, staging, production setup

The packages available in these catalogs are fixed. Multiple installations at different times will always result in exactly the same version of all operators being installed.  By choosing the same version of the catalog across multiple clusters the user is guaranteed that their installations are identical, right down to the patch level of the operators installed.  Updates can be rolled out in a controlled manner, and the upgrade path between two catalog versions will always be identical regardless of how much time passes between upgrades in different clusters.

#### Disconnected Install
> I want to run a disconnected environment using a private mirror registry

The MAS CLI [mirror-images](../guides/image-mirroring.md) function is the easiest way to mirror the content from a specific version of the Maximo Operator Catalog.  Once the images are mirrored simply run the [configure-airgap](../commands/configure-airgap.md) function to add the IBM Maximo Application Suite **ImageDigestMirrorset** to your cluster before starting the installation.


### Dynamic Catalog
The legacy dynamic operator catalog is only supported for Maximo Application Suite v8 releases, if you use the dynamic catalog you will always have access to the latest operator updates without updating the **CatalogSource** on your OpenShift cluster.

#### Manual Installation
`oc apply -f https://raw.githubusercontent.com/ibm-mas/cli/master/catalogs/v8-amd64.yaml`

#### Source
```yaml
apiVersion: operators.coreos.com/v1alpha1
kind: CatalogSource
metadata:
  name: ibm-operator-catalog
  namespace: openshift-marketplace
spec:
  displayName: IBM Maximo Operators (v8-amd64)
  publisher: IBM
  description: Dynamic Catalog Source for IBM Maximo Application Suite
  sourceType: grpc
  image: icr.io/cpopen/ibm-maximo-operator-catalog:v8-amd64
  priority: 90
```

