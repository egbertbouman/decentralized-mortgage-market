import { Component, OnInit, ViewContainerRef } from '@angular/core';
import { Router } from '@angular/router';

import { MarketService } from '../shared/market.service';

@Component({
    selector: 'profile',
    templateUrl: './profile.component.html',
    styleUrls: ['./profile.component.css']
})
export class ProfileComponent implements OnInit {
    profile = {};
    me;

    alert;

    constructor(private _marketService: MarketService,
                private _router: Router) { }

    ngOnInit() {
        this._marketService.getMyUser()
            .subscribe(me => {
                this.me = me;
                if (this.me.role == "FINANCIAL_INSTITUTION") {
                    this._router.navigateByUrl("/mortgages");
                }
            });
        this.loadMyProfile();
    }

    loadMyProfile() {
        this._marketService.getMyProfile()
            .subscribe(profile => { this.profile = profile; this.alert = undefined; },
                       err => this.alert = {type: 'warning', msg: 'You need to setup your profile before you can use the mortgage market.'});
    }

    onSubmit(event) {
        event.preventDefault();
        this.profile['role'] = this.me.role;
        // TODO
        this.profile['document_list'] = [];
        this._marketService.saveMyProfile(this.profile)
            .subscribe(() => this.loadMyProfile());
    }

}
