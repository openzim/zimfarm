import { Component, OnInit, ElementRef, ViewChild } from '@angular/core';
import { Chart, LinearChartData } from 'chart.js';

@Component({
    selector: 'task-progress',
    templateUrl: 'app/dashboard/task-progress/tasks-progress.component.html'
})
export class TaskProgressComponent implements OnInit {
    @ViewChild('taskProgress') canvas: ElementRef;
    chart: Chart;
    
    ngOnInit() {
        this.configureChart();
        this.chart.update();
    }

    configureChart(): void {
        let context: CanvasRenderingContext2D = this.canvas.nativeElement.getContext("2d");
        let data = {
            labels: [
                "Completed",
                "Executing",
                "Scheduled"
            ],
            datasets: [
                {
                    data: [300, 50, 100],
                    backgroundColor: [
                        "#FF6384",
                        "#36A2EB",
                        "#FFCE56"
                    ],
                    hoverBackgroundColor: [
                        "#FF6384",
                        "#36A2EB",
                        "#FFCE56"
                    ]
                }]
        };
        let options = {

        }
        this.chart = new Chart(context, {type: 'doughnut', data: data});
    }
}