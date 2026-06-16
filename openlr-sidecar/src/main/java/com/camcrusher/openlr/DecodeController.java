package com.camcrusher.openlr;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
public class DecodeController {

    @Autowired
    private OpenLRService openLRService;

    @PostMapping("/decode")
    public DecodeResponse decode(@RequestBody DecodeRequest request) {
        return openLRService.decode(request.getOpenlr());
    }

    @GetMapping("/health")
    public String health() {
        return "OK";
    }
}
