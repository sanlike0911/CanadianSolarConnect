# CanadaSolarConnect
This project is a system that accesses the API server operating on CanadianSolar power units to retrieve power information. Verified power detection unit: CSPDUE

## Item Description

**Note:** The following parameter descriptions are based on analysis and reverse-engineering, as official documentation is not publicly available. They are not confirmed by the manufacturer.

| No | Item Name  | Description (Unofficial)                                              |
|----|------------|-----------------------------------------------------------------------|
| 1  | ipaddress  | Address of the power detection unit (CSPDUE)                          |
| 2  | 24080038   | Serial number of the unit                                             |
| 3  | PC1f7eed87-b | Session ID (may vary)                                                 |
| 4  | 20250206&20250206 | Start and end date for the query (YYYYMMDD)                      |
| 5  | Z02        | Request sequence number                                               |
| 6  | V2HST      | History status (?)                                                    |
| 7  | DST        | Daylight Saving Time setting                                          |
| 8  | IEVD       | Inverter DC Voltage [V]                                               |
| 9  | IEVC       | Inverter DC Current [A]                                               |
| 10 | IEVR       | Inverter Power [W]                                                    |
| 11 | IG0        | Instantaneous Generated Power [kW]                                    |
| 12 | IBE        | Instantaneous Purchased Power [kW]                                    |
| 13 | ISE        | Instantaneous Sold Power [kW]                                         |
| 14 | ICE        | Instantaneous Consumed Power [kW]                                     |
| 15 | TG0        | Total Generated Power [kWh]                                           |
| 16 | IDD        | Unknown                                                               |
| 17 | IDC        | Maximum DC Current [A] (?)                                            |
| 18 | IDR        | Unknown                                                               |
| 19 | IGE        | Unknown                                                               |

## API Endpoints

### GET /getinfo

Retrieve power information from the CanadianSolar power unit.

#### Query Parameters

| Parameter         | Type   | Required | Description                                                                   |
|-------------------|--------|----------|-------------------------------------------------------------------------------|
| `startDate`       | string | No       | Start date in `YYYYMMDD` format. If omitted, uses today's date automatically. |
| `endDate`         | string | No       | End date in `YYYYMMDD` format. If omitted, uses today's date automatically.   |
| `sequenceCounter` | int    | No       | Sequence counter (0-65535). If not provided, defaults to 0.                  |
| `getParams`       | string | YES      | Parameters to retrieve. Defaults to `V2HST&DST&IEVD&IEVC&IEVR&IG0&IBE&ISE&ICE&TG0&IDD&IDC&IDR&IGE`. |

**Note:** When both `startDate` and `endDate` are omitted, the API automatically retrieves data for the current date only.

#### Response

- `200 OK`: Returns the power information in JSON format.
- `4xx/5xx`: Returns an error message with the status code.

#### Example Request

```
GET /getinfo?startDate=20250301&endDate=20250301&sequenceCounter=1&getParams=V2HST&DST&IEVD&IEVC&IEVR&IG0&IBE&ISE&ICE&TG0&IDD&IDC&IDR&IGE
```

#### Example Response

```json
{
  "00000000000000": null,
  "16640": null,
  "20250301": null,
  "24080038": null,
  "DST": "-2",
  "IBE": "0.0",
  "ICE": "2.0",
  "IDC": "0.0",
  "IDD": "0.0",
  "IDR": "0",
  "IEVC": "-1",
  "IEVD": "-1",
  "IEVR": "0",
  "IG0": "3.4",
  "IGE": "3380",
  "ISE": "1.4",
  "TG0": "6.0",
  "V2HST": "-2",
  "Z1": null
}
