import { Component, HostBinding, OnInit } from '@angular/core';

import { Icons } from '../../../shared/enum/icons.enum';
import { Permissions } from '../../../shared/models/permissions';
import { AuthStorageService } from '../../../shared/services/auth-storage.service';
import {
  FeatureTogglesMap$,
  FeatureTogglesService
} from '../../../shared/services/feature-toggles.service';
import { SummaryService } from '../../../shared/services/summary.service';

@Component({
  selector: 'cd-navigation',
  templateUrl: './navigation.component.html',
  styleUrls: ['./navigation.component.scss']
})
export class NavigationComponent implements OnInit {
  @HostBinding('class.isPwdDisplayed') isPwdDisplayed = false;

  permissions: Permissions;
  enabledFeature$: FeatureTogglesMap$;
  summaryData: any;
  icons = Icons;

  isCollapsed = true;
  showMenuSidebar = true;
  displayedSubMenu = '';

  simplebar = {
    autoHide: false
  };

  constructor(
    private authStorageService: AuthStorageService,
    private summaryService: SummaryService,
    private featureToggles: FeatureTogglesService
  ) {
    this.permissions = this.authStorageService.getPermissions();
    this.enabledFeature$ = this.featureToggles.get();
  }

  ngOnInit() {
    this.summaryService.subscribe((data: any) => {
      if (!data) {
        return;
      }
      this.summaryData = data;
    });
    this.authStorageService.isPwdDisplayed$.subscribe((isDisplayed) => {
      this.isPwdDisplayed = isDisplayed;
    });
  }

  blockHealthColor() {
    if (this.summaryData && this.summaryData.rbd_mirroring) {
      if (this.summaryData.rbd_mirroring.errors > 0) {
        return { color: '#d9534f' };
      } else if (this.summaryData.rbd_mirroring.warnings > 0) {
        return { color: '#f0ad4e' };
      }
    }

    return undefined;
  }

  toggleSubMenu(menu: string) {
    if (this.displayedSubMenu === menu) {
      this.displayedSubMenu = '';
    } else {
      this.displayedSubMenu = menu;
    }
  }
}
